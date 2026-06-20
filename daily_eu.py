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
        import math
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None


SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY = datetime.now().strftime("%Y-%m-%d")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

SUFFIX_MAP = {"MIL":".MI","XETRA":".DE","PA":".PA","AS":".AS","MC":".MC","BR":".BR","LS":".LS","VI":".VI","HE":".HE","IR":".IR","AT":".AT","LSE":".L","AIM":".L","SWX":".SW","OM":".ST","NGM":".ST","OB":".OL","CPSE":".CO"}
SPECIAL_TICKERS = {"BP.":"BP.L","RR.":"RR.L","BT.A":"BT-A.L","BA.":"BA.L","NG.":"NG.L","AO.":"AO.L","VP.":"VP.L","QQ.":"QQ.L","SN.":"SN.L"}

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
print("="*60)
print(f"FORWARDALPHA DAILY EU LOAD — {TODAY}")
print("="*60)

all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","in_universe":"eq.true","exchange":"not.eq.US","offset":str(offset),"limit":"1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"Universo EU: {len(all_stocks)} titoli")

print("\n[1/4] Download prezzi EOD...")
ok = fail = 0
price_buf = []
for stock in all_stocks:
    ticker = stock["ticker"]; exchange = stock["exchange"]; s = sym(ticker, exchange)
    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,close","ticker":"eq."+ticker,"exchange":"eq."+exchange,"order":"date.desc","limit":"1"})
    data = r.json()
    last = data[0]["date"] if data else "2021-05-25"
    last_close_db = data[0]["close"] if data else None
    if last >= TODAY: ok += 1; continue
    start = (datetime.strptime(last,"%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        df = yf.download(s, start=start, end=TODAY, progress=False, auto_adjust=True)
        if df.empty: raise Exception("empty")
        if hasattr(df.columns,"get_level_values"): df.columns=df.columns.get_level_values(0)
        df = df.reset_index()
        if last_close_db and len(df) > 0:
            first_new = safe_float(df.iloc[0]["Close"])
            if first_new and abs(first_new/last_close_db - 1) > 0.35:
                print(f" SPLIT rilevato {ticker}: DB={last_close_db} Yahoo={first_new:.4f}")
                requests.delete(SUPABASE_URL+"/rest/v1/prices_eod",
                    headers={**headers_r,"Content-Type":"application/json"},
                    params={"ticker":"eq."+ticker,"exchange":"eq."+exchange})
                df = yf.download(s, start="2021-01-01", end=TODAY, progress=False, auto_adjust=True)
                if df.empty: raise Exception("empty after split")
                if hasattr(df.columns,"get_level_values"): df.columns=df.columns.get_level_values(0)
                df = df.reset_index()
        for _,row in df.iterrows():
            cv = safe_float(row["Close"])
            if cv is None: continue
            price_buf.append({"ticker":ticker,"exchange":exchange,"date":row["Date"].strftime("%Y-%m-%d"),"open":safe_float(row.get("Open",cv)) or cv,"high":safe_float(row.get("High",cv)) or cv,"low":safe_float(row.get("Low",cv)) or cv,"close":cv,"adj_close":cv,"volume":safe_int(row.get("Volume",0))})
        ok += 1
    except: fail += 1
    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        price_buf = []
    if (ok+fail) % 200 == 0: print(f" prezzi ok={ok} fail={fail}")
    time.sleep(0.05)
if price_buf:
    requests.post(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_up, json=price_buf)
print(f" Prezzi: ok={ok} fail={fail}")
ok_prices = ok; fail_prices = fail

from datetime import datetime as dt, timedelta

print("\n Calcolo momentum...")
ok = fail = 0; mom_updates = []
for stock in all_stocks:
    ticker = stock["ticker"]; exchange = stock["exchange"]
    # Legge prezzi con paginazione per avere tutta la serie storica
    data = []
    offset_p = 0
    while True:
        rp = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":"eq."+ticker,"exchange":"eq."+exchange,
                    "date":"lte."+TODAY,"order":"date.desc","offset":str(offset_p),"limit":"1000"})
        chunk = rp.json()
        if not chunk: break
        data.extend(chunk)
        if len(chunk) < 1000: break
        offset_p += 1000
        if len(data) >= 1826: break
    data = data[:1826]
    if not data: fail+=1; continue
    data = [d for d in data if d["adj_close"]]
    if not data: fail+=1; continue

    last_px = data[0]["adj_close"]
    last_date = dt.strptime(data[0]["date"], "%Y-%m-%d")
    chg1d = round((data[0]["adj_close"]/data[1]["adj_close"]-1)*100,4) if len(data)>=2 else None

    def mom_cal(days):
        target = last_date - timedelta(days=days)
        closest = min(data, key=lambda x: abs((dt.strptime(x["date"],"%Y-%m-%d")-target).days))
        if closest["adj_close"] and closest["adj_close"] != 0:
            return round(last_px/closest["adj_close"]-1, 6)
        return None

    mom_updates.append({
        "ticker":ticker,"exchange":exchange,
        "mom1w":mom_cal(7),"mom1m":mom_cal(31),
        "mom6m":mom_cal(182),"mom12m":mom_cal(365),
        "change1d":chg1d
    })
    ok += 1
for i in range(0,len(mom_updates),100):
    requests.post(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_up, json=mom_updates[i:i+100])
print(f" Momentum ok={ok} fail={fail}")
ok_momentum = ok


print("\n Aggiornamento prezzo corrente in stocks...")
price_updates = []
for stock in all_stocks:
    ticker = stock["ticker"]; exchange = stock["exchange"]
    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,close","ticker":"eq."+ticker,"exchange":"eq."+exchange,
                "order":"date.desc","limit":"1"})
    data = r.json()
    if data:
        price_updates.append({
            "ticker": ticker, "exchange": exchange,
            "price": data[0]["close"],
            "last_price_date": data[0]["date"]
        })
saved_prices = 0
for d in price_updates:
    r2 = requests.patch(SUPABASE_URL+"/rest/v1/stocks",
        headers=headers_up,
        params={"ticker":f"eq.{d['ticker']}","exchange":f"eq.{d['exchange']}"},
        json={"price": d["price"], "last_price_date": d["last_price_date"]})
    if r2.status_code in (200,201,204): saved_prices += 1
print(f" Prezzi correnti aggiornati: {saved_prices}/{len(price_updates)}")

print("\n[2/4] Cambi FX...")
FX_PAIRS = {"EURGBP=X":"EURGBP","EURCHF=X":"EURCHF","EURSEK=X":"EURSEK","EURNOK=X":"EURNOK","EURDKK=X":"EURDKK","EURUSD=X":"EURUSD","GBPUSD=X":"GBPUSD"}
fx_rates = {"date": TODAY}
for pair_sym, pair_name in FX_PAIRS.items():
    try:
        info = yf.Ticker(pair_sym).info
        fx_rates[pair_name] = info.get("regularMarketPrice") or info.get("previousClose")
    except: pass
    time.sleep(0.2)
requests.post(SUPABASE_URL+"/rest/v1/fx_rates", headers=headers_up, json=[fx_rates])
print(" FX salvati")

print("\n[3/4] Ricalcolo rank EU...")
all_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m","exchange":"not.in.(US,TSE,SEHK,TSX,ASX)","in_universe":"eq.true","offset":str(offset),"limit":"1000"})
    data = r.json()
    if not data: break
    all_data.extend(data); offset += 1000
    if len(data) < 1000: break

mom_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mom1w,mom1m","exchange":"not.in.(US,TSE,SEHK,TSX,ASX)","in_universe":"eq.true","offset":str(offset),"limit":"1000"})
    data = r.json()
    if not data: break
    mom_data.extend(data); offset += 1000
    if len(data) < 1000: break

mom1w_map = {(d["ticker"],d["exchange"]):d.get("mom1w") for d in mom_data}
mom1m_map = {(d["ticker"],d["exchange"]):d.get("mom1m") for d in mom_data}

RANK_GROUPS = {"ITA":["MIL"],"DEU":["XETRA"],"FRA":["PA"],"GBR":["LSE"],"SWE":["OM"],"NOR":["OB"],"CHE":["SWX"],"NLD":["AS"],"BEL":["BR"],"FIN":["HE"],"ESP":["MC"],"DNK":["CPSE"]}
NO_RANK = {"AT","VI","LS","IR","NGM","AIM"}

def calc_ranks(group):
    ey_trail_g=[ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g=[ey(d["pe_forward"]) for d in group if ey(d["pe_forward"]) is not None]
    pb_g=[d["pb"] for d in group if d["pb"] is not None and not math.isnan(float(d["pb"]))]
    eps_g_vals=[d["eps_growth"] for d in group if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
    rev_g_vals=[d["rev_growth"] for d in group if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]
    mom6_adj_g=[]; mom12_adj_g=[]
    for d in group:
        key=(d["ticker"],d["exchange"]); m6=d.get("mom6m"); m12=d.get("mom12m"); m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
        if m6 is not None and m1w is not None: mom6_adj_g.append(m6-m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12-m1m)
    pre=[]
    for d in group:
        key=(d["ticker"],d["exchange"]); pe_t=d.get("pe_trailing"); pe_f=d.get("pe_forward"); pb_v=d.get("pb")
        eps_g=d.get("eps_growth"); rev_g=d.get("rev_growth")
        m6=d.get("mom6m"); m12=d.get("mom12m"); m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
        ey_t=ey(pe_t); r_eyt=pct_rank(ey_trail_g,ey_t) if ey_t is not None else None
        ey_f=ey(pe_f); r_eyf=pct_rank(ey_fwd_g,ey_f) if ey_f is not None else None
        r_pb=(100-pct_rank(pb_g,pb_v)) if pb_v is not None and pb_g else None
        r_epsg=pct_rank(eps_g_vals,eps_g) if eps_g is not None else None
        r_revg=pct_rank(rev_g_vals,rev_g) if rev_g is not None else None
        mom6_adj=(m6-m1w) if m6 is not None and m1w is not None else None
        mom12_adj=(m12-m1m) if m12 is not None and m1m is not None else None
        r_m6=pct_rank(mom6_adj_g,mom6_adj) if mom6_adj is not None else None
        r_m12=pct_rank(mom12_adj_g,mom12_adj) if mom12_adj is not None else None
        pre.append({"ticker":d["ticker"],"exchange":d["exchange"],"r_eyt":r_eyt,"r_eyf":r_eyf,"r_pb":r_pb,"r_epsg":r_epsg,"r_revg":r_revg,"r_m6":r_m6,"r_m12":r_m12})
    val_sums=[sum(x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None) for p in pre if len([x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None])>=2]
    gr_sums=[sum(x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None) for p in pre if len([x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None])>=3]
    results=[]
    for p in pre:
        val_inputs=[x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None]
        gr_inputs=[x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None]
        value_score=int(round(pct_rank(val_sums,sum(val_inputs)))) if len(val_inputs)>=2 and val_sums else None
        growth_score=int(round(pct_rank(gr_sums,sum(gr_inputs)))) if len(gr_inputs)>=3 and gr_sums else None
        results.append({"ticker":p["ticker"],"exchange":p["exchange"],"value_score":value_score,"growth_score":growth_score,"rank_pe_ltm":p["r_eyt"],"rank_pe_ntm":p["r_eyf"],"rank_pb":p["r_pb"],"rank_eps_gr":p["r_epsg"],"rank_rev_gr":p["r_revg"],"rank_mom6_adj":p["r_m6"],"rank_mom12_adj":p["r_m12"]})
    return results

rank_updates=[]
for country,exchanges in RANK_GROUPS.items():
    group=[d for d in all_data if d["exchange"] in exchanges]
    if group: rank_updates.extend(calc_ranks(group))
ranked_exchanges=set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked=[d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked: rank_updates.extend(calc_ranks(unranked))

ok=0
for i in range(0,len(rank_updates),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_up,json=rank_updates[i:i+100])
    if r.status_code in (200,201,204): ok+=len(rank_updates[i:i+100])
print(f" Rank: {ok}/{len(rank_updates)}")

requests.patch(SUPABASE_URL+"/rest/v1/fundamentals",headers={**headers_up,"Prefer":"return=minimal"},params={"exchange":"not.eq.US"},json={"combined_rank":None})
all_scores=[d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr_eu=[d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates=[{"ticker":d["ticker"],"exchange":d["exchange"],"combined_rank":min(99,pct_rank(sum_arr_eu,d["value_score"]+d["growth_score"]))} for d in all_scores]
ok=0
for i in range(0,len(combined_updates),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_up,json=combined_updates[i:i+100])
    if r.status_code in (200,201,204): ok+=len(combined_updates[i:i+100])
print(f" Combined rank EU: {ok}/{len(combined_updates)}")
ok_rank=ok


# ── AGGIORNAMENTO INDICI EU ──────────────────────────────────
print("\n Aggiornamento indici EU...")

EU_INDICES = [
    ("GDAXI.INDX", "XETRA", "DAX", "DAX"),
    ("FCHI.INDX", "PA", "FCHI", "CAC 40"),
    ("AEX.INDX", "AS", "AEX", "AEX"),
    ("IBEX.INDX", "MC", "IBEX", "IBEX 35"),
    ("BFX.INDX", "BR", "BFX", "BEL 20"),
    ("^FTSE", "LSE", "FTSE", "FTSE 100"),
    ("SSMI.INDX", "SWX", "SMI", "SMI"),
    ("OMXS30.INDX","OM", "OMXS30", "OMX Stockholm"),
    ("OMXC25.INDX","CPSE", "C25", "OMX Copenhagen"),
    ("ATX.INDX", "VI", "ATX", "ATX"),
    ("ISEQ.INDX", "IR", "IEX", "ISEQ"),
    ("STOXX50E.INDX","EZ", "SX5E", "Euro Stoxx 50"),
    ("SXXP.INDX", "EZ", "SXXP.INDX", "STOXX 600"),
    ("OMXHPI.INDX","HE", "HEX", "OMX Helsinki"),
    ("FTSEMIB.MI", "MIL", "MIB", "FTSE MIB"),
    ("PSI20.INDX", "LS", "PSI", "PSI 20"),
]

ok_idx = 0
for db_ticker, exchange, leeway_ticker, name in EU_INDICES:
    # Scarica ultimo prezzo da Leeway
    url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={TODAY}&to={TODAY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if not data:
            # Prova ieri
            ieri = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            url2 = f"https://api.leeway.tech/api/v1/public/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={ieri}&to={TODAY}"
            r2 = requests.get(url2, timeout=10)
            data = r2.json() if r2.status_code == 200 and isinstance(r2.json(), list) else []
        if not data: continue

        # Salva in price_history
        rows = [{"ticker": db_ticker, "exchange": exchange,
                 "date": d["date"], "close": d["adjusted_close"]}
                for d in data if d.get("adjusted_close")]
        if rows:
            requests.post(SUPABASE_URL+"/rest/v1/price_history",
                headers=headers_up, json=rows)

        # Calcola change1d
        price = data[-1]["adjusted_close"]
        change1d = None
        if len(data) >= 2:
            change1d = round((data[-1]["adjusted_close"]/data[-2]["adjusted_close"]-1)*100, 2)
        else:
            # Leggi prezzo precedente da price_history
            r_prev = requests.get(SUPABASE_URL+"/rest/v1/price_history", headers=headers_r,
                params={"select":"close","ticker":f"eq.{db_ticker}","exchange":f"eq.{exchange}",
                        "order":"date.desc","limit":"2"})
            prev_data = r_prev.json()
            if len(prev_data) >= 2:
                change1d = round((price/prev_data[1]["close"]-1)*100, 2)

        # Aggiorna tabella indices
        requests.patch(SUPABASE_URL+"/rest/v1/indices", headers=headers_up,
            params={"ticker": f"eq.{db_ticker}"},
            json={"price": price, "change1d": change1d, "date": data[-1]["date"]})
        print(f" {name}: {price} ({change1d}%)")
        ok_idx += 1
    except Exception as e:
        print(f" ERR {name}: {e}")
    time.sleep(0.2)

print(f" Indici EU aggiornati: {ok_idx}/{len(EU_INDICES)}")

end_time=time_module.time()
log_entry={"run_date":TODAY,"market":"EU","prices_updated":ok_prices,"prices_failed":fail_prices,"last_price_date":TODAY,"momentum_updated":ok_momentum,"rank_updated":ok_rank,"duration_seconds":int(end_time-start_time)}
requests.post(SUPABASE_URL+"/rest/v1/daily_log",headers=headers_up,json=[log_entry])
print(f"\nLog: prezzi={ok_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n"+"="*60)
print("DAILY EU LOAD COMPLETATO")
print("="*60)
