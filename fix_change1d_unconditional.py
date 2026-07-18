import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

ALL_EXCHANGES = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS","TSE","SEHK","ASX","KRX","SGX"]

# Ricalcolo diretto da prices_eod, senza passare per la scrittura precedente
# (piu' sicuro che tentare di "indovinare" quali valori dividere per 100)
total_fixed = 0
for ex in ALL_EXCHANGES:
    universe = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        universe.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    updates = []
    for stock in universe:
        ticker, exchange = stock["ticker"], stock["exchange"]
        try:
            r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
                params={"select":"adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"2"}, timeout=15)
            rows = r2.json()
            if not isinstance(rows, list) or len(rows) < 2:
                continue
            last_p, prev_p = rows[0]["adj_close"], rows[1]["adj_close"]
            if not last_p or not prev_p:
                continue
            # RAW DECIMAL, come da convenzione: NESSUN *100 qui
            change1d = round(last_p/prev_p - 1, 6)
            updates.append({"ticker": ticker, "exchange": exchange, "change1d": change1d})
        except Exception:
            continue

    if updates:
        ok = 0
        for i in range(0, len(updates), 200):
            chunk = updates[i:i+200]
            resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204): ok += len(chunk)
        print(f"{ex}: {ok}/{len(updates)} ricalcolati direttamente (raw decimal)")
        total_fixed += ok

print(f"\nTOTALE ricalcolati: {total_fixed}")
