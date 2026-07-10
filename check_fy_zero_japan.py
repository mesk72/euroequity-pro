import os, requests, csv, io
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Titoli TSE in universo
tse_tickers = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.TSE","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    tse_tickers.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break
print(f"Titoli TSE in universo: {len(tse_tickers)}")

r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
fy_map = {}
for row in reader:
    if row.get("exchange","").strip() == "TSE":
        fy_map[row["ticker"].strip()] = row.get("fiscal_month","").strip()

zero_count = 0
missing_count = 0
month_dist = Counter()
for t in tse_tickers:
    fm = fy_map.get(t)
    if fm is None:
        missing_count += 1
    elif fm == "0":
        zero_count += 1
    else:
        month_dist[fm] += 1

print(f"fiscal_month = 0 (invalido): {zero_count}")
print(f"Non presenti affatto in fiscal_year_end.csv: {missing_count}")
print(f"Distribuzione mesi validi: {dict(month_dist)}")
