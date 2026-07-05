import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
fieldnames = reader.fieldnames

print("Tutte le colonne che contengono '2029' o '2030':")
for f in fieldnames:
    if "2029" in f or "2030" in f:
        print(" ", repr(f))

print("\nRiga MU, tutti i campi con 2029/2030:")
for row in reader:
    if row.get("Ticker", "").strip() == "MU":
        for k, v in row.items():
            if "2029" in k or "2030" in k:
                print(f"  {k}: {v}")
        break
