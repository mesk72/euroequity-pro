import os, requests, csv, io
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
rows = list(reader)
c = Counter(row.get("Primary Exchange","").strip() for row in rows)
print("Distinct Primary Exchange values nel nuovo file TIKR NA:")
for val, cnt in c.most_common(20):
    print(f"  {val!r}: {cnt}")

print()
rf = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
print("fiscal_year_end.csv primi 300 char:")
print(rf.text[:300])
readerf = csv.DictReader(io.StringIO(rf.text))
frows = list(readerf)
print(f"\nColonne fiscal_year_end.csv: {list(frows[0].keys()) if frows else 'N/A'}")
print(f"Righe totali: {len(frows)}")
cf = Counter(row.get("exchange","").strip() for row in frows)
print("Distinct 'exchange' values in fiscal_year_end.csv:")
for val, cnt in cf.most_common(20):
    print(f"  {val!r}: {cnt}")
print("Primi 3 righe complete:")
for row in frows[:3]:
    print(" ", row)
