import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

total_written = 0
for ex in ALL_RANKED:
    # Un giorno alla volta, dal piu' recente indietro, finche' non ho
    # raccolto 2 prezzi per ogni ticker di quel mercato - stesso principio
    # sicuro gia' usato stanotte per evitare di tagliare a meta' un giorno
    # tra titoli diversi con la paginazione.
    by_ticker = {}
    for days_back in range(10):
        import datetime
        d = (datetime.date.today() - datetime.timedelta(days=days_back)).isoformat()
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker,date,adj_close","exchange":f"eq.{ex}","date":f"eq.{d}"})
        rows = r.json()
        if not isinstance(rows, list): continue
        for row in rows:
            key = row["ticker"]
            if key not in by_ticker: by_ticker[key] = []
            if len(by_ticker[key]) < 2:
                by_ticker[key].append({"date": row["date"], "price": row["adj_close"]})

    rows_to_write = []
    for tk, prices in by_ticker.items():
        if not prices: continue
        latest = prices[0]
        prev = prices[1] if len(prices) > 1 else None
        change1d = (latest["price"] / prev["price"] - 1) if prev and prev["price"] else None
        rows_to_write.append({
            "ticker": tk, "exchange": ex,
            "price": latest["price"], "prev_price": prev["price"] if prev else None,
            "price_date": latest["date"], "change1d": round(change1d, 6) if change1d is not None else None,
        })

    for i in range(0, len(rows_to_write), 500):
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_up, json=rows_to_write[i:i+500])
        if r2.status_code not in (200, 201, 204):
            print(f"  ERRORE scrittura {ex} batch {i}: {r2.status_code} {r2.text[:200]}")
    total_written += len(rows_to_write)
    print(f"{ex}: {len(rows_to_write)} titoli scritti")

print(f"\nTOTALE: {total_written} titoli scritti in latest_prices")
