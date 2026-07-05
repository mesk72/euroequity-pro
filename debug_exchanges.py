import os, requests, csv, io
from collections import Counter

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

exchanges_seen = Counter()
dia_rows = []
for row in reader:
    exchanges_seen[row.get("exchange", "").strip()] += 1
    if row.get("ticker", "").strip().upper() == "DIA":
        dia_rows.append(dict(row))

print("Righe con ticker DIA:")
for d in dia_rows:
    print(" ", d)

print(f"\nTop 40 valori 'exchange' più frequenti nel file (su {sum(exchanges_seen.values())} righe totali):")
for exch, count in exchanges_seen.most_common(40):
    print(f"  {exch}: {count}")
