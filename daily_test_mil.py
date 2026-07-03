import os, requests, time
from datetime import datetime, timedelta

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

print(f"=== DAILY TEST MIL — {TODAY} ===")
print()

# ── 1. Carica titoli in universe ─────────────────────────────
stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{EXCHANGE}",
                "in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    stocks.extend([s["ticker"] for s in batch])
    offset += 1000
    if len(batch)<1000: break

print(f"[1/4] Titoli in universe {EXCHANGE}: {len(stocks)}")

# ── 2. Scarica prezzi mancanti da Leeway ─────────────────────
print(f"[2/4] Download prezzi da Leeway...")

# Carica ultimo prezzo in DB per ogni titolo (bulk)
last_dates = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker,date","exchange":f"eq.{EXCHANGE}",
                "order":"date.desc","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for row in batch:
        t = row["ticker"]
        if t not in last_dates:
            last_dates[t] = row["date"]
    offset += 1000
    if len(batch)<1000: break

print(f"  Titoli con prezzi in DB: {len(last_dates)}")

ok = fail = 0
rows_to_insert = []

# Cancella prezzi esistenti MIL per riscaricamento pulito
print("  Cancello prezzi esistenti MIL...")
r_del = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod",
    headers=headers_up,
    params={"exchange": f"eq.{EXCHANGE}"})
print(f"  Delete: HTTP {r_del.status_code}")

for ticker in stocks:
    leeway_ticker = f"{ticker}{LEEWAY_SUFFIX}"
    # Scarica sempre 5 anni completi per evitare problemi con dati corrotti
    from_date = FROM_5Y
    url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={from_date}&to={TODAY}"

    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            prices = r.json()
            for p in prices:
                adj = p.get("adjusted_close") or p.get("close")
                if not adj: continue
                rows_to_insert.append({
                    "ticker": ticker, "exchange": EXCHANGE,
                    "date": p["date"], "adj_close": float(adj)
                })
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {ticker}: HTTP {r.status_code}")
    except Exception as e:
        fail += 1
        print(f"  FAIL {ticker}: {e}")

    if len(rows_to_insert) >= 2000:
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers={**headers_up, "Prefer": "resolution=merge-duplicates,return=minimal"}, json=rows_to_insert)
        print(f"  >>> Salvate {len(rows_to_insert)} righe: HTTP {r2.status_code}")
        rows_to_insert = []

    time.sleep(0.5)

if rows_to_insert:
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
        headers=headers_up, json=rows_to_insert)
    print(f"  >>> Salvate {len(rows_to_insert)} righe finali: HTTP {r2.status_code}")

print(f"  Prezzi: ok={ok} fail={fail}")

# ── 3. Calcola momentum ──────────────────────────────────────
print(f"[3/4] Calcolo momentum...")

TODAY_DT = datetime.strptime(TODAY, "%Y-%m-%d")
D1W  = (TODAY_DT - timedelta(days=7)).strftime("%Y-%m-%d")
D1M  = (TODAY_DT - timedelta(days=30)).strftime("%Y-%m-%d")
D6M  = (TODAY_DT - timedelta(days=182)).strftime("%Y-%m-%d")
D12M = (TODAY_DT - timedelta(days=365)).strftime("%Y-%m-%d")

mom_ok = mom_fail = 0

for ticker in stocks:
    # Carica prezzi degli ultimi 13 mesi
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}",
                "exchange":f"eq.{EXCHANGE}","date":f"gte.{D12M}",
                "order":"date.asc","limit":"300"})
    prices = r.json()
    if not isinstance(prices, list) or len(prices) < 2:
        mom_fail += 1
        if mom_fail <= 3:
            print(f"  FAIL momentum {ticker}: {r.status_code} rows={len(prices) if isinstance(prices,list) else type(prices)} resp={str(prices)[:100]}")
        continue

    price_map = {p["date"]: p["adj_close"] for p in prices}
    last_price = prices[-1]["adj_close"]
    last_date  = prices[-1]["date"]

    def nearest(target):
        candidates = [d for d in price_map if d <= target]
        if not candidates: return None
        return price_map[max(candidates)]

    p1w  = nearest(D1W)
    p1m  = nearest(D1M)
    p6m  = nearest(D6M)
    p12m = nearest(D12M)

    def pct(old):
        if old and old > 0: return round((last_price - old) / old, 4)
        return None

    fund_update = {
        "mom1w":  pct(p1w),
        "mom1m":  pct(p1m),
        "mom6m":  pct(p6m),
        "mom12m": pct(p12m),
        "price":  round(last_price, 4),
        "last_price_date": last_date,
    }

    r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker":f"eq.{ticker}","exchange":f"eq.{EXCHANGE}"},
        json=fund_update)
    if r2.status_code in (200,204): mom_ok += 1
    else: mom_fail += 1

print(f"  Momentum: ok={mom_ok} fail={mom_fail}")

# ── 4. Calcola rank momentum e value/growth ──────────────────
print(f"[4/4] Calcolo rank...")

# Carica tutti i fondamentali MIL in universe
all_data = []
offset = 0
universe_keys = set(stocks)
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange":f"eq.{EXCHANGE}",
                "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_data.extend([d for d in batch if d["ticker"] in universe_keys])
    offset += 1000
    if len(batch)<1000: break

print(f"  Titoli con fondamentali: {len(all_data)}")

def pct_rank(values, ascending=True):
    valid = [(i,v) for i,v in enumerate(values) if v is not None]
    n = len(valid)
    if n == 0: return {i: None for i in range(len(values))}
    sorted_vals = sorted(valid, key=lambda x: x[1], reverse=not ascending)
    ranks = {}
    for rank_pos, (orig_idx, val) in enumerate(sorted_vals):
        ranks[orig_idx] = round((rank_pos + 0.5) / n * 100)
    return {i: ranks.get(i) for i in range(len(values))}

# Calcola rank momentum
mom6m_vals  = [d.get("mom6m")  for d in all_data]
mom12m_vals = [d.get("mom12m") for d in all_data]
mom1w_vals  = [d.get("mom1w")  for d in all_data]
mom1m_vals  = [d.get("mom1m")  for d in all_data]

r6m  = pct_rank(mom6m_vals)
r12m = pct_rank(mom12m_vals)
r1w  = pct_rank(mom1w_vals)
r1m  = pct_rank(mom1m_vals)

rank_ok = rank_fail = 0
for i, d in enumerate(all_data):
    ticker = d["ticker"]
    update = {
        "rank_mom6_adj":  r6m.get(i),
        "rank_mom12_adj": r12m.get(i),
    }
    r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker":f"eq.{ticker}","exchange":f"eq.{EXCHANGE}"},
        json=update)
    if r2.status_code in (200,204): rank_ok += 1
    else: rank_fail += 1

print(f"  Rank momentum: ok={rank_ok} fail={rank_fail}")
print(f"\n=== DONE MIL ===")
print(f"Vai su forwardalpha.pro/screen/Italy per verificare")
