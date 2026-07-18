import os, requests, time

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

NA_EXCHANGES = ["US","TSX"]

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

universe = get_universe(NA_EXCHANGES)
print(f"Universo NA totale: {len(universe)} titoli", flush=True)

updates = []
errors = 0
processed = 0

for stock in universe:
    ticker, exchange = stock["ticker"], stock["exchange"]
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                     "order":"date.desc","limit":"25"}, timeout=15)
        rows = r.json()
        if not isinstance(rows, list) or len(rows) < 22:
            continue
        last_price = rows[0]["adj_close"]
        p_1w = rows[5]["adj_close"]
        p_1m = rows[21]["adj_close"]
        if not last_price or not p_1w or not p_1m:
            continue
        updates.append({"ticker": ticker, "exchange": exchange,
                         "mom1w": round(last_price/p_1w-1,6), "mom1m": round(last_price/p_1m-1,6), "price": last_price})
    except Exception as e:
        errors += 1

    processed += 1
    if processed % 200 == 0:
        print(f"  Processati {processed}/{len(universe)} | calcolati {len(updates)} | errori {errors}", flush=True)

    # Scrittura periodica ogni 500 per non perdere tutto in caso di interruzione
    if len(updates) >= 500:
        ok = 0
        for i in range(0, len(updates), 200):
            chunk = updates[i:i+200]
            resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204):
                ok += len(chunk)
        print(f"  Scrittura parziale: {ok}/{len(updates)} salvati", flush=True)
        updates = []

# Scrittura finale del resto
if updates:
    ok = 0
    for i in range(0, len(updates), 200):
        chunk = updates[i:i+200]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204):
            ok += len(chunk)
    print(f"  Scrittura finale: {ok}/{len(updates)} salvati", flush=True)

print(f"COMPLETATO. Processati {processed}/{len(universe)}, errori {errors}", flush=True)
