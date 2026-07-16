import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

EU_EXCHANGES = ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS']

total_fixed = total_skipped = 0
for ex in EU_EXCHANGES:
    # Universo in_universe=true
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
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{ex}","order":"date.desc","limit":"2"})
        prices = r2.json()
        if len(prices) < 2:
            total_skipped += 1
            continue
        p_today, p_prev = prices[0]["adj_close"], prices[1]["adj_close"]
        if not p_today or not p_prev or p_prev == 0:
            total_skipped += 1
            continue
        change1d = round(p_today / p_prev - 1, 6)
        updates.append({"ticker": ticker, "exchange": ex, "change1d": change1d, "price": p_today})

    ok = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i+100]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204):
            ok += len(chunk)
        else:
            print(f"  WARN {ex}: HTTP {resp.status_code} {resp.text[:150]}")
    print(f"{ex}: {ok}/{len(updates)} ricalcolati da prices_eod fresco")
    total_fixed += ok

print(f"\nTOTALE ricalcolati: {total_fixed} | saltati (storico insufficiente): {total_skipped}")
