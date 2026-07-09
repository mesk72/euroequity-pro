import os, requests, csv, io
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_gcc_latest.csv", headers=headers_r)
print(f"HTTP {r.status_code}, {len(r.text)} bytes")
if r.status_code != 200:
    print(r.text[:300])
else:
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    print(f"Righe totali: {len(rows)}")
    print(f"Colonne: {list(rows[0].keys()) if rows else 'N/A'}")
    c = Counter(row.get("Primary Exchange","").strip() for row in rows)
    print("Distinct Primary Exchange:")
    for val, cnt in c.most_common(20):
        print(f"  {val!r}: {cnt}")
    ccountry = Counter(row.get("Country","").strip() for row in rows)
    print("Distinct Country (se presente):")
    for val, cnt in ccountry.most_common(20):
        print(f"  {val!r}: {cnt}")
    print("\nPrime 3 righe complete:")
    for row in rows[:3]:
        print(" ", row)
