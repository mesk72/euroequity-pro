import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json"}

def leeway_ticker(ticker):
    return ticker.rstrip(".").replace(".", "-") + ".US"

# 1. Trova tutti i titoli US in_universe con prezzo fermo prima dell'8 luglio
all_us = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_us.extend(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break
print(f"Universo US totale: {len(all_us)}")

stale = []
for i in range(0, len(all_us), 1000):
    chunk = all_us[i:i+1000]
    # per ciascun ticker, ultima data
    for t in chunk:
        pass  # placeholder, query singola sotto per efficienza reale

# Query piu' efficiente: prendi tutte le ultime date con una sola chiamata per pagina
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker,date","exchange":"eq.US","date":"gte.2026-07-08","order":"ticker"})
fresh_tickers = set()
offset = 0
while True:
    rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","date":"gte.2026-07-08","limit":"1000","offset":str(offset)})
    batch = rr.json()
    if not isinstance(batch,list) or not batch: break
    fresh_tickers.update(row["ticker"] for row in batch)
    offset += 1000
    if len(batch) < 1000: break

stale = [t for t in all_us if t not in fresh_tickers]
print(f"Titoli US fermi (< 8 luglio): {len(stale)}")

ok = fail = 0
price_buf = []
for i, ticker in enumerate(stale):
    yt = leeway_ticker(ticker)
    try:
        url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            fail += 1
            continue
        data = r.json()
        if not isinstance(data, list) or not data:
            fail += 1
            continue
        for row in data:
            adj = row.get("adjusted_close") or row.get("close")
            if adj is None or float(adj) >= 999999: continue
            price_buf.append({"ticker": ticker, "exchange": "US", "date": row["date"], "adj_close": float(adj)})
        ok += 1
    except Exception:
        fail += 1
    if len(price_buf) >= 500:
        resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf, timeout=30)
        if resp.status_code not in (200,201,204):
            print(f"  WARN batch: HTTP {resp.status_code} {resp.text[:150]}")
        price_buf = []
    if (i+1) % 100 == 0:
        print(f"  ...{i+1}/{len(stale)} — ok={ok} fail={fail}")
    time.sleep(0.3)

if price_buf:
    resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf, timeout=30)
    print(f"  Ultimo batch: HTTP {resp.status_code}")

print(f"\nFINALE: ok={ok} fail={fail} su {len(stale)} titoli fermi processati")
