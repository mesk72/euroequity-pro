import os, requests, time
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

NA_EXCHANGES = ["US","TSX"]
APAC_EXCHANGES = ["TSE","SEHK","ASX","KRX","SGX"]
ALL_EX = NA_EXCHANGES + APAC_EXCHANGES

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

universe = get_universe(ALL_EX)
print(f"Universo totale NA+APAC: {len(universe)} titoli")

# Scarica prices_eod in blocchi grandi (ultimi 30gg), per exchange, paginato
all_prices = defaultdict(list)  # key: (ticker,exchange) -> list of (date, adj_close)
for ex in ALL_EX:
    offset = 0
    count_ex = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker,exchange,date,adj_close","exchange":f"eq.{ex}",
                     "order":"ticker.asc,date.desc","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for row in batch:
            key = (row["ticker"], row["exchange"])
            if len(all_prices[key]) < 25:  # bastano i primi 25 giorni più recenti per titolo
                all_prices[key].append((row["date"], row["adj_close"]))
        count_ex += len(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"  {ex}: {count_ex} righe prezzo scaricate")

print(f"Totale chiavi (ticker,exchange) con dati prezzo: {len(all_prices)}")

updates = []
for (ticker, exchange), rows in all_prices.items():
    rows_sorted = sorted(rows, key=lambda x: x[0], reverse=True)
    if len(rows_sorted) < 22:
        continue
    last_price = rows_sorted[0][1]
    p_1w = rows_sorted[5][1] if len(rows_sorted) > 5 else None
    p_1m = rows_sorted[21][1] if len(rows_sorted) > 21 else None
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
