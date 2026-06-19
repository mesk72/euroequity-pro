# ============================================================
# FORWARDALPHA — DAILY LOAD
# Da eseguire ogni sera dopo la chiusura dei mercati europei
# Tempo stimato: 35-40 minuti
# ============================================================

import yfinance as yf
import requests
import pandas as pd
import numpy as np
import json
import time
import math
import os
import time as time_module
from datetime import datetime, timedelta

# ── CONFIGURAZIONE ──────────────────────────────────────────
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY = datetime.now().strftime("%Y-%m-%d")

headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

SUFFIX_MAP = {
    "MIL":".MI","XETRA":".DE","PA":".PA","AS":".AS","MC":".MC",
    "BR":".BR","LS":".LS","VI":".VI","HE":".HE","IR":".IR","AT":".AT",
    "LSE":".L","AIM":".L","SWX":".SW","OM":".ST","NGM":".ST",
    "OB":".OL","CPSE":".CO"
}
SPECIAL_TICKERS = {
    "BP.":"BP.L","RR.":"RR.L","BT.A":"BT-A.L","BA.":"BA.L",
    "NG.":"NG.L","AO.":"AO.L","VP.":"VP.L","QQ.":"QQ.L","SN.":"SN.L",
}

def sym(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    return ticker.replace(" ","-") + SUFFIX_MAP.get(exchange,"")

def safe_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except: return None

def safe_int(v):
    try:
        f = float(v)
        return 0 if math.isnan(f) or math.isinf(f) else int(f)
    except: return 0

def ts(t):
    try: return datetime.fromtimestamp(t).strftime("%Y-%m-%d")
    except: return None

# ── LEGGE UNIVERSO ──────────────────────────────────────────
start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA DAILY LOAD — {TODAY}")
print("=" * 60)

all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","offset":offset,"limit":1000})
    data = r.json()
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"\nUniverso: {len(all_stocks)} titoli")

# ============================================================
# STEP 1 — PREZZI EOD + MOMENTUM
# ============================================================
print("\n[1/5] Download prezzi EOD...")

ok_prices=0
fail_prices=0
ok=fail=0
price_buf=[]

for stock in all_stocks:
    ticker = stock["ticker"]
    exchange = stock["exchange"]
    s = sym(ticker, exchange)

    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":"eq."+ticker,"exchange":"eq."+exchange,
                "order":"date.desc","limit":1})
    data = r.json()
    last = data[0]["date"] if data else "2021-05-25"

    if last >= TODAY:
        ok += 1
        continue

    start = (datetime.strptime(last,"%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        df = yf.download(s, start=start, end=TODAY, progress=False, auto_adjust=True)
        if df.empty: raise Exception("empty")
        if hasattr(df.columns,"get_level_values"): df.columns=df.columns.get_level_values(0)
        df = df.reset_index()
        for _,row in df.iterrows():
            cv = safe_float(row["Close"])
            if cv is None: continue
            price_buf.append({
                "ticker":ticker,"exchange":exchange,
                "date":row["Date"].strftime("%Y-%m-%d"),
                "open":safe_float(row.get("Open",cv)) or cv,
                "high":safe_float(row.get("High",cv)) or cv,
                "low":safe_float(row.get("Low",cv)) or cv,
                "close":cv,"adj_close":cv,
                "volume":safe_int(row.get("Volume",0))
            })
        ok += 1
    except: fail += 1

    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL+"/rest/v1/prices_eod",
            headers=headers_up, json=price_buf)
        price_buf = []
    if (ok+fail) % 200 == 0:
        print(f" prezzi ok={ok} fail={fail}")
    time.sleep(0.05)

if price_buf:
    requests.post(SUPABASE_URL+"/rest/v1/prices_eod",
        headers=headers_up, json=price_buf)
print(f" Prezzi completati: ok={ok} fail={fail}")

# ── CALCOLA MOMENTUM ────────────────────────────────────────
print("\n Calcolo momentum...")
ok=fail=0
mom_updates=[]

for stock in all_stocks:
    ticker = stock["ticker"]
    exchange = stock["exchange"]

    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":"eq."+ticker,
                "exchange":"eq."+exchange,"date":"lte."+TODAY,
                "order":"date.desc","limit":260})
    data = r.json()
    if not data: fail+=1; continue

    closes = [d["adj_close"] for d in data if d["adj_close"]]
    if not closes: fail+=1; continue

    last_px = closes[0]

    def mom(n):
        if len(closes) >= n and closes[n-1]:
            return round(last_px/closes[n-1]-1, 6)
        return None

    chg1d = round((closes[0]/closes[1]-1)*100, 4) if len(closes)>=2 else None

    mom_updates.append({
        "ticker":ticker,"exchange":exchange,
        "mom1w":mom(5),"mom1m":mom(21),
        "mom6m":mom(126),"mom12m":mom(252),
        "change1d":chg1d
    })
    ok+=1

for i in range(0,len(mom_updates),100):
    requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=mom_updates[i:i+100])
print(f" Momentum ok={ok} fail={fail}")

# Step 2 earnings rimosso — aggiornato manualmente con CSV TIKR

# ============================================================
# STEP 3 — CAMBI FX
# ============================================================
print("\n[3/5] Download cambi FX...")

FX_PAIRS = {
    "EURGBP=X":"EURGBP","EURCHF=X":"EURCHF","EURSEK=X":"EURSEK",
    "EURNOK=X":"EURNOK","EURDKK=X":"EURDKK","EURUSD=X":"EURUSD",
    "GBPUSD=X":"GBPUSD"
}
fx_rates = {"date": TODAY}
for pair_sym, pair_name in FX_PAIRS.items():
    try:
        info = yf.Ticker(pair_sym).info
        rate = info.get("regularMarketPrice") or info.get("previousClose")
        fx_rates[pair_name] = rate
        print(f" {pair_name}: {rate}")
    except: pass
    time.sleep(0.2)

requests.post(SUPABASE_URL+"/rest/v1/fx_rates",
    headers=headers_up, json=[fx_rates])
print(" Cambi FX salvati")

# ============================================================
# STEP 4 — CARICA CSV TIKR E CALCOLA FONDAMENTALI
# ============================================================
print("\n[4/5] Carica CSV TIKR e calcola fondamentali...")

from google.colab import files
uploaded = files.upload()
csv_name = list(uploaded.keys())[0]
df = pd.read_csv(csv_name)
print(f" CSV caricato: {len(df)} righe")

def parse_num(v):
    if v is None: return None
    try:
        import pandas as pd
        if pd.isna(v): return None
    except: pass
    s = str(v).strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    s = s.replace('$','').replace(',','').replace('x','').replace('%','').strip()
    if s in ['-', '', 'N/A', 'nm', chr(8212)]: return None
    try:
        import math
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None


def pct_rank(values,v,invert=False):
    if v is None: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    valid=[x for x in values if x is not None]
    if not valid: return None
    below=sum(1 for x in valid if x<v)
    rank=below/len(valid)*100
    return int(round(100-rank if invert else rank))

def ey(pe):
    if pe is None or pe == 0: return None
    try:
        if isinstance(pe, float) and math.isnan(pe): return None
    except: return None
    if abs(pe)>200: return None
    return 1.0/pe

def calc_ranks_for_group(group):
    ey_trail_g =[ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g =[ey(d["pe_forward"]) for d in group if ey(d["pe_forward"]) is not None]
    pb_g =[d["pb"] for d in group if d["pb"] is not None and not math.isnan(float(d["pb"])) and d["pb"]<50]
    eps_g_vals =[d["eps_growth"] for d in group if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
    rev_g_vals =[d["rev_growth"] for d in group if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]
    mom6_adj_g =[]
    mom12_adj_g=[]
    for d in group:
        key=(d["ticker"],d["exchange"])
        m6=d.get("mom6m"); m12=d.get("mom12m")
        m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
        if m6 is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)

    results = []
    for d in group:
        key = (d["ticker"], d["exchange"])
        pe_t = d.get("pe_trailing")
        pe_f = d.get("pe_forward")
        pb_v = d.get("pb")
        eps_g = d.get("eps_growth")
        rev_g = d.get("rev_growth")
        m6 = d.get("mom6m")
        m12 = d.get("mom12m")
        m1w = mom1w_map.get(key)
        m1m = mom1m_map.get(key)

        ey_t = ey(pe_t)
        if ey_t is not None:
            r_eyt = pct_rank(ey_trail_g, ey_t)
        elif pe_t is not None and pe_t < 0:
            r_eyt = 1
        else:
            r_eyt = None

        ey_f = ey(pe_f)
        if ey_f is not None:
            r_eyf = pct_rank(ey_fwd_g, ey_f)
        elif pe_f is not None and pe_f < 0:
            r_eyf = 1
        else:
            r_eyf = None

        r_pb = pct_rank([1/x for x in pb_g if x > 0], 1/pb_v if pb_v and pb_v > 0 else None) if pb_v and pb_v > 0 else None

        val_inputs = [x for x in [r_eyt, r_eyf, r_pb] if x is not None]
        value_score = int(round(sum(val_inputs)/len(val_inputs))) if val_inputs else None

        r_epsg = pct_rank(eps_g_vals, eps_g) if eps_g is not None else None
        r_revg = pct_rank(rev_g_vals, rev_g) if rev_g is not None else None
        mom6_adj = (m6 - m1w) if m6 is not None and m1w is not None else None
        mom12_adj = (m12 - m1m) if m12 is not None and m1m is not None else None
        r_m6 = pct_rank(mom6_adj_g, mom6_adj) if mom6_adj is not None else None
        r_m12 = pct_rank(mom12_adj_g, mom12_adj) if mom12_adj is not None else None

        gr_inputs = [x for x in [r_epsg, r_revg, r_m6, r_m12] if x is not None]
        growth_score = int(round(sum(gr_inputs)/len(gr_inputs))) if gr_inputs else None

        r_pe_ltm = pct_rank(ey_trail_g, ey_t) if ey_t is not None else (1 if pe_t is not None and pe_t < 0 else None)
        r_pe_ntm = pct_rank(ey_fwd_g, ey_f) if ey_f is not None else (1 if pe_f is not None and pe_f < 0 else None)
        r_pb_ind = pct_rank([1/x for x in pb_g if x > 0], 1/pb_v if pb_v and pb_v > 0 else None) if pb_v and pb_v > 0 else None
        r_eps_gr = pct_rank(eps_g_vals, eps_g) if eps_g is not None else None
        r_rev_gr = pct_rank(rev_g_vals, rev_g) if rev_g is not None else None

        results.append({
            "ticker": d["ticker"], "exchange": d["exchange"],
            "value_score": value_score,
            "growth_score": growth_score,
            "rank_pe_ltm": r_pe_ltm,
            "rank_pe_ntm": r_pe_ntm,
            "rank_pb": r_pb_ind,
            "rank_eps_gr": r_eps_gr,
            "rank_rev_gr": r_rev_gr,
        })
    return results

rank_updates = []
for country, exchanges in RANK_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if not group: continue
    rank_updates.extend(calc_ranks_for_group(group))

ranked_exchanges = set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked = [d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked:
    rank_updates.extend(calc_ranks_for_group(unranked))

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print(f" Rank aggiornati: {ok}/{len(rank_updates)}")

all_scores = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,value_score,growth_score",
                "offset":offset,"limit":1000})
    data = r.json()
    if not data: break
    all_scores.extend(data)
    offset += 1000
    if len(data) < 1000: break

# Separa EU e US per combined_rank continentale
all_scores_eu = [d for d in all_scores if d["exchange"] != "US" 
                 and d.get("value_score") is not None 
                 and d.get("growth_score") is not None]
all_scores_us = [d for d in all_scores if d["exchange"] == "US"
                 and d.get("value_score") is not None
                 and d.get("growth_score") is not None]

sum_arr_eu = [d["value_score"] + d["growth_score"] for d in all_scores_eu]
sum_arr_us = [d["value_score"] + d["growth_score"] for d in all_scores_us]

combined_updates = []
for d in all_scores_eu:
    total = d["value_score"] + d["growth_score"]
    combined_updates.append({
        "ticker": d["ticker"], "exchange": d["exchange"],
        "combined_rank": min(99, pct_rank(sum_arr_eu, total))
    })
for d in all_scores_us:
    total = d["value_score"] + d["growth_score"]
    combined_updates.append({
        "ticker": d["ticker"], "exchange": d["exchange"],
        "combined_rank": min(99, pct_rank(sum_arr_us, total))
    })

ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print(f" Combined rank aggiornati: {ok}/{len(combined_updates)}")


# ============================================================
# LOG GIORNALIERO
# ============================================================
end_time = time_module.time()
log_entry = {
    "run_date": TODAY,
    "market": os.environ.get("MARKET", "EU"),
    "prices_updated": ok,
    "prices_failed": fail,
    "last_price_date": TODAY,
    "momentum_updated": len(mom_updates),
    "rank_updated": ok,
    "duration_seconds": int(end_time - start_time)
}
requests.post(SUPABASE_URL+"/rest/v1/daily_log",
    headers=headers_up, json=[log_entry])
print(f"\nLog salvato: {log_entry}")

print("\n" + "="*60)
print("DAILY LOAD COMPLETATO")
print("="*60)
