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

# Cancella prezzi via RPC function
print("  Cancello prezzi esistenti MIL via RPC...")
r_del = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/delete_prices_by_exchange",
    headers=headers_up,
    json={"exch": EXCHANGE})
print(f"  Delete RPC: HTTP {r_del.status_code} {r_del.text[:100] if r_del.status_code not in (200,201,204) else 'OK'}")

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
    })
    ok += 1

for upd in mom_updates:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)

print(f"  Momentum: ok={ok} fail={fail}")

# ── 4. Rank momentum ─────────────────────────────────────────
print(f"[4/4] Calcolo rank...")

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

def pct_rank(values):
    valid = [(i,v) for i,v in enumerate(values) if v is not None]
    n = len(valid)
    if n==0: return {i:None for i in range(len(values))}
    sorted_v = sorted(valid,key=lambda x: x[1])
    ranks = {}
    for pos,(idx,val) in enumerate(sorted_v):
        ranks[idx] = round((pos+0.5)/n*100)
    return {i:ranks.get(i) for i in range(len(values))}

r6m  = pct_rank([d.get("mom6m")  for d in all_data])
r12m = pct_rank([d.get("mom12m") for d in all_data])

rank_updates = []
for i,d in enumerate(all_data):
    rank_updates.append({
        "ticker":d["ticker"],"exchange":d["exchange"],
        "rank_mom6_adj":r6m.get(i),"rank_mom12_adj":r12m.get(i),
    })

for upd in rank_updates:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)

print(f"  Rank calcolato per {len(rank_updates)} titoli")
print(f"\n=== DONE MIL — vai su forwardalpha.pro screen Italy ===")
