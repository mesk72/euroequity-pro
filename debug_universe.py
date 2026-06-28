import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EX_MAP = {
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "TSX":"TSX","TSXV":"TSX",
}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

total = 0
us = 0
tsx = 0
other = {}
empty = 0
duplicates = set()
seen = set()

for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, None)
    
    total += 1
    if not ticker:
        empty += 1
        continue
    if (ticker, ex_raw) in seen:
        duplicates.add((ticker, ex_raw))
    seen.add((ticker, ex_raw))
    
    if exchange == "US": us += 1
    elif exchange == "TSX": tsx += 1
    else:
        other[ex_raw] = other.get(ex_raw, 0) + 1

print(f"Totale righe CSV: {total}")
print(f"US: {us}")
print(f"TSX: {tsx}")
print(f"Righe vuote ticker: {empty}")
print(f"Duplicati: {len(duplicates)}")
print(f"Exchange non mappati ({sum(other.values())} righe): {other}")
if duplicates:
    print(f"Esempi duplicati: {list(duplicates)[:10]}")
