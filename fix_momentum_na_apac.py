import os, requests, datetime
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

NA_EXCHANGES = ["US","TSX"]
cutoff = (datetime.date.today() - datetime.timedelta(days=35)).isoformat()

all_prices = defaultdict(list)
for ex in NA_EXCHANGES:
    offset = 0
    count_ex = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker,exchange,date,adj_close","exchange":f"eq.{ex}","date":f"gte.{cutoff}",
                     "order":"ticker.asc,date.desc","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list):
            print(f"  ERRORE {ex} offset {offset}: {batch}")
            break
        if not batch: break
        for row in batch:
            all_prices[(row["ticker"], row["exchange"])].append((row["date"], row["adj_close"]))
        count_ex += len(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"  {ex}: {count_ex} righe scaricate (ultimi 35gg)")

print(f"Chiavi totali: {len(all_prices)}")

updates = []
for (ticker, exchange), rows in all_prices.items():
    rows_sorted = sorted(rows, key=lambda x: x[0], reverse=True)
    if len(rows_sorted) < 22:
        continue
    last_price = rows_sorted[0][1]
    p_1w = rows_sorted[5][1]
    p_1m = rows_sorted[21][1]
    if not last_price or not p_1w or not p_1m:
        continue
    updates.append({"ticker": ticker, "exchange": exchange,
                     "mom1w": round(last_price/p_1w-1,6), "mom1m": round(last_price/p_1m-1,6), "price": last_price})

print(f"Calcolati: {len(updates)}")

ok = 0
for i in range(0, len(updates), 200):
    chunk = updates[i:i+200]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=chunk, timeout=30)
    if resp.status_code in (200,201,204):
        ok += len(chunk)
    else:
        print(f"  WARN: HTTP {resp.status_code} {resp.text[:150]}")
print(f"TOTALE scritti: {ok}/{len(updates)}")
