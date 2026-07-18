import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

ALL_EXCHANGES = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS","TSE","SEHK","ASX","KRX","SGX"]

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
print(f"Universo totale tutti i mercati: {len(universe)} titoli", flush=True)

updates = []
errors = 0
processed = 0

for stock in universe:
    ticker, exchange = stock["ticker"], stock["exchange"]
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                     "order":"date.desc","limit":"2"}, timeout=15)
        rows = r.json()
        if not isinstance(rows, list) or len(rows) < 2:
            processed += 1
            continue
        last_price = rows[0]["adj_close"]
        prev_price = rows[1]["adj_close"]
        if not last_price or not prev_price:
            processed += 1
            continue
        change1d = round((last_price/prev_price - 1) * 100, 4)
        updates.append({"ticker": ticker, "exchange": exchange, "change1d": change1d, "price": last_price})
    except Exception:
        errors += 1

    processed += 1
    if processed % 300 == 0:
        print(f"  {processed}/{len(universe)} | calcolati {len(updates)} | errori {errors}", flush=True)

    if len(updates) >= 500:
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

print(f"COMPLETATO. Processati {processed}, errori {errors}", flush=True)
