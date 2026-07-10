import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
us_rows = [row for row in reader if row["exchange"] == "US"]
print(f"Righe US nel file: {len(us_rows)}")

# Confronta con universo US reale
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1"},
    headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"})
print("Universo US totale:", r2.headers.get("content-range"))

from collections import Counter
c = Counter(row["fiscal_month"] for row in us_rows)
print("Distribuzione mesi (primi 15):", c.most_common(15))
zero = c.get("0",0) + c.get("",0)
print(f"Invalidi (0/vuoto): {zero}")
