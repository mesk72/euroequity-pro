import os, requests, datetime
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import subprocess
    subprocess.run(["pip","install","python-dateutil","--break-system-packages","-q"])
    from dateutil.relativedelta import relativedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

ALL_EXCHANGES = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS","TSE","SEHK","ASX","KRX","SGX"]

def find_ref_date(prices_desc, target_date):
    candidates = [p for p in prices_desc if p["date"] >= target_date.isoformat()]
    if not candidates: return None
    return min(candidates, key=lambda p: p["date"])

def get_universe(exchanges):
    out = []
    for ex in exchanges:
        offset = 0
        while True:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
                params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
            batch = r.json()
            if not isinstance(batch,list) or not batch: break
            out.extend(batch)
            offset += 1000
            if len(batch) < 1000: break
    return out

universe = get_universe(ALL_EXCHANGES)
print(f"Universo totale: {len(universe)} titoli", flush=True)

updates = []
errors = 0
processed = 0

for stock in universe:
    ticker, exchange = stock["ticker"], stock["exchange"]
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                     "order":"date.desc","limit":"800"}, timeout=15)
        prices = r.json()
        if not isinstance(prices, list) or len(prices) < 260:
            processed += 1
            continue

        today_price = prices[0]["adj_close"]
        today_date = datetime.date.fromisoformat(prices[0]["date"])

        # 1 settimana: 4 posizioni indietro (verificato con Yahoo)
        p1w = prices[4]["adj_close"] if len(prices) > 4 else None

        # 1/6/12 mesi: calendario + 1gg, snap al primo trading day disponibile
        vals = {}
        for months, key in [(1,"mom1m"), (6,"mom6m"), (12,"mom12m")]:
            target = today_date - relativedelta(months=months)
            target_plus1 = target + datetime.timedelta(days=1)
            ref = find_ref_date(prices, target_plus1)
            vals[key] = ref["adj_close"] if ref else None

        mom1w = round(today_price/p1w - 1, 6) if p1w else None
        mom1m = round(today_price/vals["mom1m"] - 1, 6) if vals["mom1m"] else None
        mom6m = round(today_price/vals["mom6m"] - 1, 6) if vals["mom6m"] else None
        mom12m = round(today_price/vals["mom12m"] - 1, 6) if vals["mom12m"] else None

        if mom1w is None or mom1m is None or mom6m is None or mom12m is None:
            processed += 1
            continue

        updates.append({"ticker": ticker, "exchange": exchange,
                         "mom1w": mom1w, "mom1m": mom1m, "mom6m": mom6m, "mom12m": mom12m,
                         "price": today_price})
    except Exception:
        errors += 1

    processed += 1
    if processed % 300 == 0:
        print(f"  {processed}/{len(universe)} | calcolati {len(updates)} | errori {errors}", flush=True)

    if len(updates) >= 400:
        ok = 0
        for i in range(0, len(updates), 200):
            chunk = updates[i:i+200]
            resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204): ok += len(chunk)
        print(f"  Scrittura parziale: {ok}/{len(updates)}", flush=True)
        updates = []

if updates:
    ok = 0
    for i in range(0, len(updates), 200):
        chunk = updates[i:i+200]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204): ok += len(chunk)
    print(f"  Scrittura finale: {ok}/{len(updates)}", flush=True)

print(f"COMPLETATO. Processati {processed}, errori {errors}", flush=True)
