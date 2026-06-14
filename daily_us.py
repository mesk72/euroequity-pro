import yfinance as yf, requests, pandas as pd
import time, math, os, time as time_module
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY = datetime.now().strftime("%Y-%m-%d")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

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
        if math.isnan(float(pe)): return None
    except: return None
    return 1.0 / pe

start_time = time_module.time()
print("="*60)
print(f"FORWARDALPHA DAILY US LOAD — {TODAY}")
print("="*60)

all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","in_universe":"eq.true","exchange":"eq.US","offset":str(offset),"limit":"1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"Universo US: {len(all_stocks)} titoli")

print("\n[1/3] Download prezzi EOD...")
ok = fail = 0
price_buf = []
for stock in all_stocks:
 ticker = stock["ticker"]; exchange = stock["exchange"]
 r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
 params={"select":"date,close","ticker":"eq."+ticker,"exchange":"eq."+exchange,"order":"date.desc","limit":"1"})
 data = r.json()
 last = data[0]["date"] if data else "2021-05-25"
 last_close_db = data[0]["close"] if data else None
 if last >= TODAY: ok += 1; continue
 start = (datetime.strptime(last,"%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
 try:
 df = yf.download(ticker, start=start, end=TODAY, progress=False, auto_adjust=True)
 if df.empty: raise Exception("empty")
 if hasattr(df.columns,"get_level_values"): df.columns=df.columns.get_level_values(0)
 df = df.reset_index()
 # Controllo split al 35%
 if last_close_db and len(df) > 0:
 first_new = safe_float(df.iloc[0]["Close"])
 if first_new and abs(first_new/last_close_db - 1) > 0.35:
 print(f" SPLIT rilevato {ticker}: DB={last_close_db} Yahoo={first_new:.4f} — riscarico 5 anni")
 requests.delete(SUPABASE_URL+"/rest/v1/prices_eod",
 headers={**headers_r,"Content-Type":"application/json"},
 params={"ticker":"eq."+ticker,"exchange":"eq."+exchange})
 df = yf.download(ticker, start="2021-01-01", end=TODAY, progress=False, auto_adjust=True)
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

print("\n[2/3] Ricalcolo rank US...")
all_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m","exchange":"eq.US","offset":str(offset),"limit":"1000"})
    data = r.json()
    if not data: break
    all_data.extend(data); offset += 1000
    if len(data) < 1000: break

# Filtra solo titoli in_universe
universe_keys = {f"{s['ticker']}.{s['exchange']}" for s in all_stocks}
all_data = [d for d in all_data if f"{d['ticker']}.{d['exchange']}" in universe_keys]
print(f" Fondamentali US filtrati: {len(all_data)}")

mom_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mom1w,mom1m","exchange":"eq.US","offset":str(offset),"limit":"1000"})
    data = r.json()
    if not data: break
    mom_data.extend(data); offset += 1000
    if len(data) < 1000: break

mom1w_map = {(d["ticker"],d["exchange"]):d.get("mom1w") for d in mom_data}
mom1m_map = {(d["ticker"],d["exchange"]):d.get("mom1m") for d in mom_data}

ey_trail_g=[ey(d["pe_trailing"]) for d in all_data if ey(d["pe_trailing"]) is not None]
ey_fwd_g=[ey(d["pe_forward"]) for d in all_data if ey(d["pe_forward"]) is not None]
pb_g=[d["pb"] for d in all_data if d["pb"] is not None and not math.isnan(float(d["pb"])) and d["pb"]<50]
eps_g_vals=[d["eps_growth"] for d in all_data if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
rev_g_vals=[d["rev_growth"] for d in all_data if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]
mom6_adj_g=[]; mom12_adj_g=[]
for d in all_data:
    key=(d["ticker"],d["exchange"]); m6=d.get("mom6m"); m12=d.get("mom12m"); m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
    if m6 is not None and m1w is not None: mom6_adj_g.append(m6-m1w)
    if m12 is not None and m1m is not None: mom12_adj_g.append(m12-m1m)

rank_updates=[]
for d in all_data:
    key=(d["ticker"],d["exchange"]); pe_t=d.get("pe_trailing"); pe_f=d.get("pe_forward"); pb_v=d.get("pb"); eps_g=d.get("eps_growth"); rev_g=d.get("rev_growth")
    m6=d.get("mom6m"); m12=d.get("mom12m"); m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
    ey_t=ey(pe_t); r_eyt=pct_rank(ey_trail_g,ey_t) if ey_t is not None else (1 if pe_t is not None and pe_t<0 else None)
    ey_f=ey(pe_f); r_eyf=pct_rank(ey_fwd_g,ey_f) if ey_f is not None else (1 if pe_f is not None and pe_f<0 else None)
    r_pb=pct_rank([1/x for x in pb_g if x>0],1/pb_v if pb_v and pb_v>0 else None) if pb_v and pb_v>0 else None
    val_inputs=[x for x in [r_eyt,r_eyf,r_pb] if x is not None]
 value_score=int(round(sum(val_inputs)/len(val_inputs))) if len(val_inputs)>=2 else None
    r_epsg=pct_rank(eps_g_vals,eps_g) if eps_g is not None else None
    r_revg=pct_rank(rev_g_vals,rev_g) if rev_g is not None else None
    mom6_adj=(m6-m1w) if m6 is not None and m1w is not None else None
    mom12_adj=(m12-m1m) if m12 is not None and m1m is not None else None
    r_m6=pct_rank(mom6_adj_g,mom6_adj) if mom6_adj is not None else None
    r_m12=pct_rank(mom12_adj_g,mom12_adj) if mom12_adj is not None else None
    gr_inputs=[x for x in [r_epsg,r_revg,r_m6,r_m12] if x is not None]
 growth_score=int(round(sum(gr_inputs)/len(gr_inputs))) if len(gr_inputs)>=3 else None
    rank_updates.append({"ticker":d["ticker"],"exchange":d["exchange"],"value_score":value_score,"growth_score":growth_score,"rank_pe_ltm":r_eyt,"rank_pe_ntm":r_eyf,"rank_pb":r_pb,"rank_eps_gr":r_epsg,"rank_rev_gr":r_revg})

ok=0
for i in range(0,len(rank_updates),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_up,json=rank_updates[i:i+100])
    if r.status_code in (200,201,204): ok+=len(rank_updates[i:i+100])
print(f" Rank: {ok}/{len(rank_updates)}")

all_scores=[d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr_us=[d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates=[{"ticker":d["ticker"],"exchange":d["exchange"],"combined_rank":min(99,pct_rank(sum_arr_us,d["value_score"]+d["growth_score"]))} for d in all_scores]
ok=0
for i in range(0,len(combined_updates),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_up,json=combined_updates[i:i+100])
    if r.status_code in (200,201,204): ok+=len(combined_updates[i:i+100])
print(f" Combined rank US: {ok}/{len(combined_updates)}")
ok_rank=ok

end_time=time_module.time()
log_entry={"run_date":TODAY,"market":"US","prices_updated":ok_prices,"prices_failed":fail_prices,"last_price_date":TODAY,"momentum_updated":ok_momentum,"rank_updated":ok_rank,"duration_seconds":int(end_time-start_time)}
requests.post(SUPABASE_URL+"/rest/v1/daily_log",headers=headers_up,json=[log_entry])
print(f"\nLog: prezzi={ok_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n"+"="*60)
print("DAILY US LOAD COMPLETATO")
print("="*60)
