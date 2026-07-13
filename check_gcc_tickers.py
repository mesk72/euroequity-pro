import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_gcc_latest.csv", headers=headers_r)
text = r.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))
rows = list(reader)
print(f"Righe totali nel file GCC: {len(rows)}")
print(f"Colonne: {reader.fieldnames}")
print("\nPrime 15 righe (ticker, borsa, paese, nome):")
for row in rows[:15]:
    print(f"  {row.get('Ticker')} | {row.get('Primary Exchange')} | {row.get('Country')} | {row.get('Company Name')}")

# Distribuzione per paese/borsa
from collections import Counter
countries = Counter(row.get('Country','?') for row in rows)
exchanges = Counter(row.get('Primary Exchange','?') for row in rows)
print("\nDistribuzione paesi:", dict(countries))
print("Distribuzione borse:", dict(exchanges))
