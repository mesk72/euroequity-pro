import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Universo US reale
us_universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    us_universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break
print(f"Universo US reale: {len(us_universe)}")

# Righe US nel file fiscal_year_end.csv
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
fy_us_tickers = set(row["ticker"] for row in reader if row["exchange"] == "US")
print(f"Ticker US nel file fiscal_year_end: {len(fy_us_tickers)}")

overlap = us_universe & fy_us_tickers
print(f"In comune (overlap reale): {len(overlap)}")
missing = us_universe - fy_us_tickers
print(f"Titoli del nostro universo SENZA dato fiscale: {len(missing)}")
print(f"Esempio mancanti: {list(missing)[:15]}")
