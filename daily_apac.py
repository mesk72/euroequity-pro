# ============================================================
# FORWARDALPHA — DAILY APAC LOAD
# Da eseguire ogni giorno alle 09:00 CET (mercati Asia chiusi)
# Copre: TSE (Giappone), SEHK (Hong Kong), ASX (Australia)
# ============================================================

import os
import math
import time
import time as time_module
import requests
import yfinance as yf
from datetime import datetime, timedelta

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
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
TODAY        = datetime.now().strftime("%Y-%m-%d")

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

# Suffix yfinance per exchange APAC
SUFFIX_MAP = {
    "TSE":  ".T",
    "SEHK": ".HK",
    "ASX":  ".AX",
}

def sym(ticker, exchange):
    return ticker + SUFFIX_MAP.get(exchange, "")

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

def pct_rank(values, v):
    if v is None: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    valid = [x for x in values if x is not None]
    if not valid: return None
    below = sum(1 for x in valid if x < v)
    return int(round(below / len(valid) * 100))

def ey(pe):
    if pe is None or pe == 0: return None
    try:
        if isinstance(pe, float) and math.isnan(pe): return None
    except: return None
    return 1.0 / pe

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA DAILY APAC LOAD — {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO APAC ──────────────────────────────────
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange", "in_universe": "eq.true",
                "exchange": "in.(TSE,SEHK,ASX)", "offset": str(offset), "limit": "1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"Universo APAC: {len(all_stocks)} titoli")

# ── 2. PREZZI EOD DA YFINANCE ───────────────────────────────
print("\n[1/4] Download prezzi EOD...")
ok = fail = 0
price_buf = []
for stock in all_stocks:
    ticker   = stock["ticker"]
    exchange = stock["exchange"]
    s        = sym(ticker, exchange)

    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date,close", "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}",
                "order": "date.desc", "limit": "1"})
    data = r.json()
    last           = data[0]["date"]   if data else "2021-01-01"
    last_close_db  = data[0]["close"]  if data else None
    if last >= TODAY: ok += 1; continue

    start = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        df = yf.download(s, start=start, end=TODAY, progress=False, auto_adjust=True)
        if df.empty: raise Exception("empty")
        if hasattr(df.columns, "get_level_values"):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        # Controllo split
        if last_close_db and len(df) > 0:
            first_new = safe_float(df.iloc[0]["Close"])
            if first_new and abs(first_new / last_close_db - 1) > 0.35:
                print(f"  SPLIT rilevato {ticker}.{exchange}: DB={last_close_db} Yahoo={first_new:.4f}")
                requests.delete(SUPABASE_URL + "/rest/v1/prices_eod",
                    headers={**headers_r, "Content-Type": "application/json"},
                    params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})
                df = yf.download(s, start="2021-01-01", end=TODAY, progress=False, auto_adjust=True)
                if df.empty: raise Exception("empty after split")
                if hasattr(df.columns, "get_level_values"):
                    df.columns = df.columns.get_level_values(0)
                df = df.reset_index()
        for _, row in df.iterrows():
            cv = safe_float(row["Close"])
            if cv is None: continue
            price_buf.append({
                "ticker": ticker, "exchange": exchange,
                "date":   row["Date"].strftime("%Y-%m-%d"),
                "open":   safe_float(row.get("Open",  cv)) or cv,
                "high":   safe_float(row.get("High",  cv)) or cv,
                "low":    safe_float(row.get("Low",   cv)) or cv,
                "close":  cv, "adj_close": cv,
                "volume": safe_int(row.get("Volume", 0)),
            })
        ok += 1
    except: fail += 1

    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        price_buf = []
    if (ok + fail) % 200 == 0: print(f"  prezzi ok={ok} fail={fail}")
    time.sleep(0.05)

if price_buf:
    requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
print(f"  Prezzi: ok={ok} fail={fail}")
ok_prices = ok; fail_prices = fail

# ── 3. MOMENTUM ─────────────────────────────────────────────
print("\n[2/4] Calcolo momentum...")
from datetime import datetime as dt, timedelta
ok = fail = 0
mom_updates = []
for stock in all_stocks:
    ticker   = stock["ticker"]
    exchange = stock["exchange"]
    data = []
    offset_p = 0
    while True:
        rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date,adj_close", "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}",
                    "date": f"lte.{TODAY}", "order": "date.desc",
                    "offset": str(offset_p), "limit": "1000"})
        chunk = rp.json()
        if not chunk: break
        data.extend(chunk)
        if len(chunk) < 1000: break
        offset_p += 1000
        if len(data) >= 1826: break
    data = data[:1826]
    if not data: fail += 1; continue
    data = [d for d in data if d["adj_close"]]
    if not data: fail += 1; continue

    last_px   = data[0]["adj_close"]
    last_date = dt.strptime(data[0]["date"], "%Y-%m-%d")
    chg1d     = round((data[0]["adj_close"] / data[1]["adj_close"] - 1) * 100, 4) if len(data) >= 2 else None

    def mom_cal(days):
        target  = last_date - timedelta(days=days)
        closest = min(data, key=lambda x: abs((dt.strptime(x["date"], "%Y-%m-%d") - target).days))
        if closest["adj_close"] and closest["adj_close"] != 0:
            return round(last_px / closest["adj_close"] - 1, 6)
        return None

    mom_updates.append({
        "ticker": ticker, "exchange": exchange,
        "mom1w": mom_cal(7), "mom1m": mom_cal(31),
        "mom6m": mom_cal(182), "mom12m": mom_cal(365),
        "change1d": chg1d,
    })
    ok += 1

for i in range(0, len(mom_updates), 100):
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=mom_updates[i:i+100])
print(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

# ── 4. AGGIORNAMENTO PREZZO CORRENTE IN STOCKS ───────────────
print("\n  Aggiornamento prezzo corrente in stocks...")
price_updates = []
for stock in all_stocks:
    ticker   = stock["ticker"]
    exchange = stock["exchange"]
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date,close", "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}",
                "order": "date.desc", "limit": "1"})
    data = r.json()
    if data:
        price_updates.append({"ticker": ticker, "exchange": exchange,
                               "price": data[0]["close"], "last_price_date": data[0]["date"]})
saved = 0
for d in price_updates:
    r2 = requests.patch(SUPABASE_URL + "/rest/v1/stocks", headers=headers_up,
        params={"ticker": f"eq.{d['ticker']}", "exchange": f"eq.{d['exchange']}"},
        json={"price": d["price"], "last_price_date": d["last_price_date"]})
    if r2.status_code in (200, 201, 204): saved += 1
print(f"  Prezzi correnti aggiornati: {saved}/{len(price_updates)}")

# ── 5. RANK APAC ─────────────────────────────────────────────
print("\n[3/4] Ricalcolo rank APAC...")

# Rank per paese: JP, HK, AU separati — combined rank JP+HK+AU insieme
APAC_GROUPS = {
    "JPN": ["TSE"],
    "HKG": ["SEHK"],
    "AUS": ["ASX"],
}

all_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m",
                "exchange": "in.(TSE,SEHK,ASX)", "in_universe": "eq.true",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not data: break
    all_data.extend(data); offset += 1000
    if len(data) < 1000: break

mom_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,mom1w,mom1m",
                "exchange": "in.(TSE,SEHK,ASX)", "in_universe": "eq.true",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not data: break
    mom_data.extend(data); offset += 1000
    if len(data) < 1000: break

mom1w_map = {(d["ticker"], d["exchange"]): d.get("mom1w") for d in mom_data}
mom1m_map = {(d["ticker"], d["exchange"]): d.get("mom1m") for d in mom_data}

def calc_ranks(group):
    ey_trail_g  = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g    = [ey(d["pe_forward"])  for d in group if ey(d["pe_forward"])  is not None]
    pb_g        = [d["pb"] for d in group if d["pb"] is not None and not math.isnan(float(d["pb"]))]
    eps_g_vals  = [d["eps_growth"] for d in group if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
    rev_g_vals  = [d["rev_growth"] for d in group if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]
    mom6_adj_g  = []
    mom12_adj_g = []
    for d in group:
        key = (d["ticker"], d["exchange"])
        m6  = d.get("mom6m"); m12 = d.get("mom12m")
        m1w = mom1w_map.get(key); m1m = mom1m_map.get(key)
        if m6  is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    pre = []
    for d in group:
        key   = (d["ticker"], d["exchange"])
        pe_t  = d.get("pe_trailing"); pe_f = d.get("pe_forward"); pb_v = d.get("pb")
        eps_g = d.get("eps_growth");  rev_g = d.get("rev_growth")
        m6    = d.get("mom6m"); m12 = d.get("mom12m")
        m1w   = mom1w_map.get(key); m1m = mom1m_map.get(key)
        ey_t  = ey(pe_t); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        ey_f  = ey(pe_f); r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
        r_pb  = (100 - pct_rank(pb_g, pb_v)) if pb_v is not None and pb_g else None
        r_epsg  = pct_rank(eps_g_vals, eps_g) if eps_g is not None else None
        r_revg  = pct_rank(rev_g_vals, rev_g) if rev_g is not None else None
        mom6_adj  = (m6  - m1w) if m6  is not None and m1w is not None else None
        mom12_adj = (m12 - m1m) if m12 is not None and m1m is not None else None
        r_m6  = pct_rank(mom6_adj_g,  mom6_adj)  if mom6_adj  is not None else None
        r_m12 = pct_rank(mom12_adj_g, mom12_adj) if mom12_adj is not None else None
        pre.append({"ticker": d["ticker"], "exchange": d["exchange"],
                    "r_eyt": r_eyt, "r_eyf": r_eyf, "r_pb": r_pb,
                    "r_epsg": r_epsg, "r_revg": r_revg, "r_m6": r_m6, "r_m12": r_m12})
    val_sums = [sum(x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None)
                for p in pre if len([x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None]) >= 2]
    gr_sums  = [sum(x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None)
                for p in pre if len([x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None]) >= 3]
    results = []
    for p in pre:
        val_inputs = [x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None]
        gr_inputs  = [x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None]
        value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs) >= 2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs) >= 3 and gr_sums  else None
        results.append({
            "ticker": p["ticker"], "exchange": p["exchange"],
            "value_score": value_score, "growth_score": growth_score,
            "rank_pe_ltm": p["r_eyt"], "rank_pe_ntm": p["r_eyf"], "rank_pb": p["r_pb"],
            "rank_eps_gr": p["r_epsg"], "rank_rev_gr": p["r_revg"],
            "rank_mom6_adj": p["r_m6"], "rank_mom12_adj": p["r_m12"],
        })
    return results

# Rank per paese
rank_updates = []
for country, exchanges in APAC_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f"  {country}: {len(res)} titoli rankati")

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print(f"  Rank paese: {ok}/{len(rank_updates)}")

# Combined rank APAC (JP+HK+AU insieme)
requests.patch(SUPABASE_URL + "/rest/v1/fundamentals",
    headers={**headers_up, "Prefer": "return=minimal"},
    params={"exchange": "in.(TSE,SEHK,ASX)"},
    json={"combined_rank": None})

all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr_ap = [d["value_score"] + d["growth_score"] for d in all_scores]
combined_updates = [{
    "ticker": d["ticker"], "exchange": d["exchange"],
    "combined_rank": min(99, pct_rank(sum_arr_ap, d["value_score"] + d["growth_score"]))
} for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print(f"  Combined rank APAC: {ok}/{len(combined_updates)}")
ok_rank = ok

# ── 6. INDICI APAC ──────────────────────────────────────────
print("\n[4/4] Aggiornamento indici APAC...")
APAC_INDICES = [
    ("^N225",  "TSE",  "Nikkei 225"),
    ("^HSI",   "SEHK", "Hang Seng"),
    ("^AXJO",  "ASX",  "ASX 200"),
    ("^HSCE",  "SEHK", "HSCEI"),
    ("^KS11",  "TSE",  "KOSPI"),
]
ok_idx = 0
for yf_ticker, exchange, name in APAC_INDICES:
    try:
        info = yf.Ticker(yf_ticker).fast_info
        price = getattr(info, 'last_price', None)
        prev  = getattr(info, 'previous_close', None)
        if not price: continue
        chg1d = round((price / prev - 1) * 100, 2) if prev else None
        print(f"  {name}: {price:.0f} ({chg1d}%)")
        ok_idx += 1
    except Exception as e:
        print(f"  ERR {name}: {e}")
    time.sleep(0.2)
print(f"  Indici APAC: {ok_idx}/{len(APAC_INDICES)}")

# ── LOG ──────────────────────────────────────────────────────
end_time = time_module.time()
log_entry = {
    "run_date": TODAY, "market": "APAC",
    "prices_updated": ok_prices, "prices_failed": fail_prices,
    "last_price_date": TODAY,
    "momentum_updated": ok_momentum, "rank_updated": ok_rank,
    "duration_seconds": int(end_time - start_time),
}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
print(f"\nLog: prezzi={ok_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n" + "=" * 60)
print("DAILY APAC LOAD COMPLETATO")
print("=" * 60)
