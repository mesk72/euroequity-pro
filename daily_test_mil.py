import os, requests, time
from datetime import datetime, timedelta
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EXCHANGE      = "MIL"
LEEWAY_SUFFIX = ".MI"
TODAY         = datetime.now().strftime("%Y-%m-%d")
FROM_5Y       = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
FROM_400D     = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

print(f"=== DAILY TEST MIL — {TODAY} ===")
print()

# ── 1. Carica titoli in universe ─────────────────────────────
all_stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","exchange":f"eq.{EXCHANGE}",
                "in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_stocks.extend(batch)
    offset += 1000
    if len(batch)<1000: break

tickers = [s["ticker"] for s in all_stocks]
print(f"[1/4] Titoli in universe {EXCHANGE}: {len(tickers)}")

# ── 2. Download prezzi da Leeway (5 anni) ────────────────────
print(f"[2/4] Download prezzi da Leeway (5 anni)...")

# Cancella prezzi ticker per ticker — evita timeout
print("  Cancello prezzi esistenti MIL (ticker per ticker)...")
del_ok = del_fail = 0
for ticker in tickers:
    r_del = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod",
        headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{EXCHANGE}"})
    if r_del.status_code in (200,204): del_ok += 1
    else: del_fail += 1
print(f"  Delete: ok={del_ok} fail={del_fail}")

ok = fail = 0
rows = []

for ticker in tickers:
    lt = f"{ticker}{LEEWAY_SUFFIX}"
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            for p in r.json():
                adj = p.get("adjusted_close") or p.get("close")
                if adj:
                    rows.append({"ticker":ticker,"exchange":EXCHANGE,
                                 "date":p["date"],"adj_close":float(adj)})
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {ticker}: HTTP {r.status_code}")
    except Exception as e:
        fail += 1
        print(f"  FAIL {ticker}: {e}")

    if len(rows) >= 2000:
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers={**headers_up, "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=rows)
        if r2.status_code not in (200,201,204):
            print(f"  WARN insert: HTTP {r2.status_code} {r2.text[:80]}")
        rows = []

    time.sleep(0.5)

if rows:
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
        headers={**headers_up, "Prefer": "resolution=merge-duplicates,return=minimal"},
        json=rows)
    if r2.status_code not in (200,201,204):
        print(f"  WARN insert finale: HTTP {r2.status_code} {r2.text[:80]}")

print(f"  Prezzi: ok={ok} fail={fail}")

# ── 3. Carica prezzi per momentum (chunk di 20, ultimi 400gg) ─
print(f"[3/4] Calcolo momentum...")

CHUNK = 20
all_ph = defaultdict(list)
for i in range(0, len(tickers), CHUNK):
    chunk = tickers[i:i+CHUNK]
    offset_p = 0
    while True:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker,date,adj_close",
                    "exchange":f"eq.{EXCHANGE}",
                    "ticker":"in.(" + ",".join(chunk) + ")",
                    "date":f"gte.{FROM_400D}",
                    "order":"ticker,date.desc",
                    "limit":"1000","offset":str(offset_p)})
        batch = rp.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch:
            if d["adj_close"] is not None:
                all_ph[(d["ticker"],EXCHANGE)].append(
                    {"date":d["date"],"close":d["adj_close"]})
        offset_p += 1000
        if len(batch)<1000: break
    time.sleep(0.02)

print(f"  Prezzi caricati: {len(all_ph)} titoli")

mom_updates = []
ok = fail = 0

for stock in all_stocks:
    ticker   = stock["ticker"]
    exchange = stock["exchange"]
    data_p   = all_ph.get((ticker,exchange),[])
    if len(data_p) < 2: fail += 1; continue

    last_px   = data_p[0]["close"]
    last_date = datetime.strptime(data_p[0]["date"],"%Y-%m-%d")
    chg1d     = round((data_p[0]["close"]/data_p[1]["close"]-1)*100,4) if data_p[1]["close"] else None

    def mom_cal(days):
        target  = last_date - timedelta(days=days)
        closest = min(data_p, key=lambda x: abs((datetime.strptime(x["date"],"%Y-%m-%d")-target).days))
        if closest["close"] and closest["close"] != 0:
            return round(last_px/closest["close"]-1,6)
        return None

    mom_updates.append({
        "ticker":ticker,"exchange":exchange,
        "mom1w":mom_cal(7),"mom1m":mom_cal(31),
        "mom6m":mom_cal(182),"mom12m":mom_cal(365),
        "change1d":chg1d,"price":last_px,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    })
    ok += 1

for upd in mom_updates:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)

print(f"  Momentum: ok={ok} fail={fail}")

# ── 4. Rank completo (value, growth, combined) ───────────────
print(f"[4/4] Calcolo rank completo...")

all_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange":f"eq.{EXCHANGE}","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe_set = set(tickers)
    all_data.extend([d for d in batch if d["ticker"] in universe_set])
    offset += 1000
    if len(batch)<1000: break

print(f"  Fondamentali caricati: {len(all_data)}")

# Funzioni helper
def ey(pe):
    if pe is None: return None
    try:
        v = float(pe)
        return round(1/v, 6) if v != 0 else None
    except: return None

def book_yield(pb):
    if pb is None: return None
    try:
        v = float(pb)
        return round(1/v, 6) if v != 0 else None
    except: return None

def pr(arr, val):
    if val is None or not arr: return None
    below = sum(1 for x in arr if x < val)
    equal = sum(1 for x in arr if x == val)
    return round((below + 0.5 * equal) / len(arr) * 100)

# Mappa momentum aggiornato
mom_map = {(d["ticker"],d["exchange"]): d for d in all_data}
for upd in mom_updates:
    key = (upd.get("ticker") or upd.get("_t"), upd.get("exchange") or upd.get("_e"))

# Calcola rank per il gruppo MIL
group = all_data

ey_trail_g  = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
ey_fwd_g    = [ey(d["pe_forward"])  for d in group if ey(d["pe_forward"])  is not None]
by_g        = [book_yield(d["pb"])  for d in group if book_yield(d["pb"]) is not None]
eps_g_vals  = [d["eps_growth"]      for d in group if d["eps_growth"] is not None]
rev_g_vals  = [d["rev_growth"]      for d in group if d["rev_growth"] is not None]

mom6_adj_g  = []
mom12_adj_g = []
for d in group:
    m6 = d.get("mom6m"); m12 = d.get("mom12m")
    m1w = d.get("mom1w"); m1m = d.get("mom1m")
    if m6 is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
    if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)

pre = []
for d in group:
    m6=d.get("mom6m"); m12=d.get("mom12m"); m1w=d.get("mom1w"); m1m=d.get("mom1m")
    ey_t=ey(d.get("pe_trailing")); r_eyt=pr(ey_trail_g,ey_t)
    ey_f=ey(d.get("pe_forward"));  r_eyf=pr(ey_fwd_g,ey_f)
    by_v=book_yield(d.get("pb")); r_pb=pr(by_g,by_v)
    r_epsg=pr(eps_g_vals,d.get("eps_growth"))
    r_revg=pr(rev_g_vals,d.get("rev_growth"))
    mom6_adj  = (m6-m1w)   if m6 is not None and m1w is not None else None
    mom12_adj = (m12-m1m)  if m12 is not None and m1m is not None else None
    r_m6  = pr(mom6_adj_g,  mom6_adj)
    r_m12 = pr(mom12_adj_g, mom12_adj)
    pre.append({"ticker":d["ticker"],"exchange":d["exchange"],
                "r_eyt":r_eyt,"r_eyf":r_eyf,"r_pb":r_pb,
                "r_epsg":r_epsg,"r_revg":r_revg,"r_m6":r_m6,"r_m12":r_m12})

val_sums = [sum(x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None)
            for p in pre if len([x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None])>=2]
gr_sums  = [sum(x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None)
            for p in pre if len([x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None])>=3]

rank_updates = []
for p in pre:
    val_inputs=[x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None]
    gr_inputs =[x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None]
    value_score  = int(round(pr(val_sums,sum(val_inputs)))) if len(val_inputs)>=2 and val_sums else None
    growth_score = int(round(pr(gr_sums, sum(gr_inputs))))  if len(gr_inputs)>=3 and gr_sums  else None
    rank_updates.append({
        "ticker":p["ticker"],"exchange":p["exchange"],
        "value_score":value_score,"growth_score":growth_score,
        "rank_pe_ltm":p["r_eyt"],"rank_pe_ntm":p["r_eyf"],"rank_pb":p["r_pb"],
        "rank_eps_gr":p["r_epsg"],"rank_rev_gr":p["r_revg"],
        "rank_mom6_adj":p["r_m6"],"rank_mom12_adj":p["r_m12"],
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    })

# Salva rank
for upd in rank_updates:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)

# Combined rank
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"]+d["growth_score"] for d in all_scores]
combined   = [{"ticker":d["ticker"],"exchange":d["exchange"],
               "combined_rank": min(99,int(round(pr(sum_arr,d["value_score"]+d["growth_score"]))))}
              for d in all_scores]
for upd in combined:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)

print(f"  Rank calcolato per {len(rank_updates)} titoli")
print(f"  Combined rank: {len(combined)} titoli")
print(f"\n=== DONE MIL — vai su forwardalpha.pro screen Italy ===")
