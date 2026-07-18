import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

EXCHANGES = ['US','TSX','TSE','SEHK','ASX','KRX','SGX']

total_fixed = total_skipped = 0
for ex in EXCHANGES:
    universe = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        universe.update(s["ticker"] for s in batch)
        offset += 1000
        if len(batch) < 1000: break

    updates = []
    for ticker in universe:
        r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{ex}","order":"date.desc","limit":"25"})
        prices = r2.json()
        if len(prices) < 22:
            total_skipped += 1
            continue
        closes = [p["adj_close"] for p in prices]
        last = closes[0]
        p_1w = closes[5] if len(closes) > 5 else None
        p_1m = closes[21] if len(closes) > 21 else None
        if not last or not p_1w or not p_1m or p_1w == 0 or p_1m == 0:
            total_skipped += 1
            continue
        mom1w = round(last/p_1w - 1, 6)
        mom1m = round(last/p_1m - 1, 6)
        updates.append({"ticker": ticker, "exchange": ex, "price": last, "mom1w": mom1w, "mom1m": mom1m})

    ok = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i+100]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204):
            ok += len(chunk)
        else:
            print(f"  WARN {ex}: HTTP {resp.status_code} {resp.text[:150]}")
    print(f"{ex}: {ok}/{len(updates)} aggiornati (price+mom1w+mom1m da prices_eod fresco)")
    total_fixed += ok

print(f"\nTOTALE aggiornati: {total_fixed} | saltati (storico insufficiente): {total_skipped}")
