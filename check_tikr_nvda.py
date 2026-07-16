import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

url = f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv"
r = requests.get(url, headers=headers_r)
content = r.text
reader = csv.DictReader(io.StringIO(content))

for row in reader:
    if row.get("Ticker","").strip().upper() == "NVDA":
        print("Riga NVDA completa:")
        for k, v in row.items():
            print(f"  {k}: {v}")
        break
else:
    print("NVDA non trovato - controllo primi 5 ticker per capire il formato")
    reader2 = csv.DictReader(io.StringIO(content))
    for i, row in enumerate(reader2):
        if i >= 5: break
        print(row.get("Ticker"))
