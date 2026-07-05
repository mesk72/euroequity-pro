import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EX_MAP_APAC = {
    "TSE": "TSE", "TYO": "TSE", "XTKS": "TSE",
    "SEHK": "SEHK", "HKG": "SEHK", "XHKG": "SEHK",
    "ASX": "ASX", "XASX": "ASX",
    "KOSE": "KRX", "KOSDAQ": "KRX",
    "SGX": "SGX", "Catalist": "SGX", "NSE": "SGX", "SPSE": "SGX", "NSX": "SGX", "XKON": "SGX",
}

r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
print("TUTTE LE COLONNE DEL FILE:")
for c in reader.fieldnames:
    print(" ", repr(c))

print()
count = 0
for row in reader:
    ex_tikr = row.get("Primary Exchange", "").strip()
    exchange = EX_MAP_APAC.get(ex_tikr, "")
    if exchange == "KRX" and count < 3:
        print(f"KRX ticker={row.get('Ticker')} — RIGA COMPLETA:")
        for k, v in row.items():
            print(f"    {k}: {v}")
        count += 1
        print()
    if count >= 3:
        break

