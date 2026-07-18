import os, requests, time
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

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

universe = get_universe(["US","TSX"])
print(f"Universo US+TSX: {len(universe)} titoli")

# FIX: query per singolo ticker (piu' lento ma niente timeout), solo ultimi 25gg
all_prices = defaultdict(list)
processed = 0
for entry in universe:
    ticker, exchange = entry["ticker"], entry["exchange"]
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"25"})
        rows = r.json()
        if isinstance(rows, list) and rows:
            all_prices[(ticker,exchange)] = [(row["date"], row["adj_close"]) for row in rows]
    except Exception:
        pass
    processed += 1
    if processed % 200 == 0:
        print(f"  ...processati {processed}/{len(universe)}")

print(f"Titoli con dati prezzo: {len(all_prices)}")

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
    mom1w = round(last_price/p_1w - 1, 6)
    mom1m = round(last_price/p_1m - 1, 6)
    updates.append({"ticker": ticker, "exchange": exchange, "mom1w": mom1w, "mom1m": mom1m, "price": last_price})

print(f"Aggiornamenti calcolati: {len(updates)}")

ok = 0
for i in range(0, len(updates), 200):
    chunk = updates[i:i+200]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=chunk, timeout=30)
    if resp.status_code in (200,201,204):
        ok += len(chunk)
    else:
        print(f"  WARN batch {i}: HTTP {resp.status_code} {resp.text[:150]}")

print(f"TOTALE scritti: {ok}/{len(updates)}")
