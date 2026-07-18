import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

NA_EXCHANGES = ['US', 'TSX']
APAC_EXCHANGES = ['TSE', 'SEHK', 'ASX', 'KRX', 'SGX']
ALL_EXCHANGES = NA_EXCHANGES + APAC_EXCHANGES

total_fixed = total_skipped = 0

for ex in ALL_EXCHANGES:
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
    skipped = 0
    for ticker in universe:
        r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{ex}","order":"date.desc","limit":"22"})
        prices = r2.json()
        if not isinstance(prices, list) or len(prices) < 6:
            skipped += 1
            continue

        last_price = prices[0]["adj_close"]
        p_1w = prices[5]["adj_close"] if len(prices) > 5 else None
        p_1m = prices[21]["adj_close"] if len(prices) > 21 else None

        if not last_price or not p_1w:
            skipped += 1
            continue

        mom1w = round(last_price / p_1w - 1, 6)
        mom1m = round(last_price / p_1m - 1, 6) if p_1m else None

        upd = {"ticker": ticker, "exchange": ex, "price": last_price, "mom1w": mom1w}
        if mom1m is not None:
            upd["mom1m"] = mom1m
        updates.append(upd)

    ok = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i+100]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204):
            ok += len(chunk)
        else:
            print(f"  WARN {ex}: HTTP {resp.status_code} {resp.text[:150]}")

    print(f"{ex}: {ok}/{len(updates)} aggiornati (price+mom1w+mom1m) | saltati per storico insufficiente: {skipped}")
    total_fixed += ok
    total_skipped += skipped

print(f"\nTOTALE aggiornati: {total_fixed} | saltati: {total_skipped}")
