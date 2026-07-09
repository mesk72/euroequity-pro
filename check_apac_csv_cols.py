import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
rows = list(reader)
print("Colonne:", list(rows[0].keys()) if rows else "N/A")
# trova una riga SGX con D05
for row in rows:
    if row.get("Ticker","").strip() == "D05":
        print("Riga D05:", row)
        break
else:
    print("D05 non trovato nel file!")
# campione righe con Primary Exchange che sembra SGX
from collections import Counter
c = Counter(row.get("Primary Exchange","").strip() for row in rows)
print("Primary Exchange distinct:", c.most_common(15))
