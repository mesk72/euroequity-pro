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
skipped_insufficient = 0
processed = 0

for stock in universe:
    ticker, exchange = stock["ticker"], stock["exchange"]
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                     "order":"date.desc","limit":"1600"}, timeout=20)
        prices = r.json()
        if not isinstance(prices, list) or len(prices) < 700:
            skipped_insufficient += 1
            processed += 1
            continue

        today_price = prices[0]["adj_close"]
        today_date = datetime.date.fromisoformat(prices[0]["date"])

        vals = {}
        for months, key in [(36,"mom3y"), (60,"mom5y")]:
            target = today_date - relativedelta(months=months)
            target_plus1 = target + datetime.timedelta(days=1)
            ref = find_ref_date(prices, target_plus1)
            vals[key] = ref["adj_close"] if ref else None

        mom3y = round(today_price/vals["mom3y"] - 1, 6) if vals["mom3y"] else None
        mom5y = round(today_price/vals["mom5y"] - 1, 6) if vals["mom5y"] else None

        if mom3y is None and mom5y is None:
            processed += 1
            continue

        upd = {"ticker": ticker, "exchange": exchange}
        if mom3y is not None: upd["mom3y"] = mom3y
        if mom5y is not None: upd["mom5y"] = mom5y
        updates.append(upd)
    except Exception:
        errors += 1

    processed += 1
    if processed % 300 == 0:
        print(f"  {processed}/{len(universe)} | calcolati {len(updates)} | insuff.storico {skipped_insufficient} | errori {errors}", flush=True)

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

print(f"COMPLETATO. Processati {processed}, insuff.storico {skipped_insufficient}, errori {errors}", flush=True)
