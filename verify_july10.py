import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def fetch_all(table, params):
    results = []
    offset = 0
    while True:
        p = dict(params)
        p["limit"] = "1000"
        p["offset"] = str(offset)
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_r, params=p, timeout=30)
        if r.status_code != 200:
            print(f"  ERRORE HTTP {r.status_code}: {r.text[:200]}")
            break
        batch = r.json()
        if not batch: break
        results.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return results

universe = fetch_all("stocks", {"select":"ticker","exchange":"eq.US","in_universe":"eq.true","order":"ticker"})
print(f"Universo US: {len(universe)}")

at_10 = fetch_all("prices_eod", {"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","order":"ticker"})
print(f"Righe con data = 10 luglio: {len(at_10)}")
tickers_at_10 = set(row["ticker"] for row in at_10)
print(f"Ticker unici al 10 luglio: {len(tickers_at_10)}")

universe_tickers = set(row["ticker"] for row in universe)
missing = universe_tickers - tickers_at_10
print(f"Mancanti al 10 luglio: {len(missing)}")
print(f"Esempio mancanti: {sorted(missing)[:20]}")
