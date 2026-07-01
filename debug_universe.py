import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
             "Prefer": "count=exact"}

print("=== IN_UNIVERSE ATTUALE NEL DB ===")
print()

ALL_EXCHANGES = [
    ("MIL","EU"),("XETRA","EU"),("PA","EU"),("LSE","EU"),
    ("OM","EU"),("SWX","EU"),("OB","EU"),("AS","EU"),
    ("MC","EU"),("BR","EU"),("CPSE","EU"),("HE","EU"),
    ("VI","EU"),("IR","EU"),("LS","EU"),
    ("US","NA"),("TSX","NA"),
    ("TSE","APAC"),("SEHK","APAC"),("ASX","APAC"),
    ("KRX","APAC"),("SGX","APAC"),
]

total_eu = total_na = total_apac = 0

for exchange, region in ALL_EXCHANGES:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{exchange}",
                "in_universe":"eq.true","limit":"1"})
    count = int(r.headers.get("content-range","0/0").split("/")[-1])
    print(f"  {exchange:<8} {region:<5} in_universe={count}")
    if region == "EU": total_eu += count
    elif region == "NA": total_na += count
    elif region == "APAC": total_apac += count

print()
print(f"  TOTALE EU:   {total_eu}")
print(f"  TOTALE NA:   {total_na}")
print(f"  TOTALE APAC: {total_apac}")
print(f"  TOTALE:      {total_eu+total_na+total_apac}")
