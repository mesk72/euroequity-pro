import os, requests, csv, io
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
us_rows = [row for row in reader if row["exchange"] == "US"]
print(f"Righe US nel file: {len(us_rows)}")

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1"})
print("Universo US totale:", r2.headers.get("content-range"))

c = Counter(row["fiscal_month"] for row in us_rows)
print("Distribuzione mesi (primi 15):", c.most_common(15))
zero = c.get("0",0) + c.get("",0)
print(f"Invalidi (0/vuoto): {zero}")
