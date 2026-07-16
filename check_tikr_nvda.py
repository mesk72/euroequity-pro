import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Scarica il file CSV TIKR NA dal bucket storage
url = f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/tikr_na_latest.csv"
r = requests.get(url)
print("Status download:", r.status_code)

if r.status_code == 200:
    content = r.text
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames
    print("Colonne trovate (prime 30):", headers[:30] if headers else "NESSUNA")

    for row in reader:
        ticker_val = row.get("Ticker") or row.get("ticker") or row.get("Symbol")
        if ticker_val and "NVDA" in str(ticker_val).upper():
            print("\nRiga NVDA trovata:")
            for k, v in row.items():
                if "eps" in k.lower() or "fy" in k.lower():
                    print(f"  {k}: {v}")
            break
    else:
        print("NVDA non trovato nel file")
else:
    print("Contenuto errore:", r.text[:300])
