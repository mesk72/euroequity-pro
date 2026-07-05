import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
print("HTTP status:", r.status_code)
reader = csv.DictReader(io.StringIO(r.text))
print("Colonne:", reader.fieldnames)

count = 0
found = []
for row in reader:
    count += 1
    if row.get("ticker", "").strip().upper() in ("MU", "MRVL"):
        found.append(dict(row))

print(f"Righe totali: {count}")
print("Righe trovate per MU/MRVL:")
for f in found:
    print(" ", f)
