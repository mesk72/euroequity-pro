import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers)
print("STATUS:", r.status_code, "SIZE:", len(r.content))

text = r.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))
headers_list = reader.fieldnames
print("Colonne disponibili:", headers_list)

found = False
for row in reader:
    ticker_val = row.get('Ticker') or row.get('ticker') or row.get('Symbol') or ''
    if 'HLF' in str(ticker_val).upper():
        print("\nRIGA TROVATA:")
        for k, v in row.items():
            print(f"  {k}: {v!r}")
        found = True
if not found:
    print("\nHLF non trovato nel file con colonna Ticker/Symbol standard, provo ricerca libera nel testo grezzo")
