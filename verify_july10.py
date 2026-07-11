import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

all_us = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_us.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break

at_july10 = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    at_july10.update(row["ticker"] for row in batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"US totale: {len(all_us)}")
print(f"US al 10 luglio esatto: {len(at_july10)}")
print(f"Mancanti: {len(all_us - at_july10)}")
