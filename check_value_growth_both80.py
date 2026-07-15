import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Universo US: {len(universe)} titoli")

count = 0
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,value_score,growth_score","exchange":"eq.US",
                 "value_score":"gte.80","growth_score":"gte.80","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe:
            count += 1
    offset += 1000
    if len(batch) < 1000: break

print(f"Titoli con Value>=80 E Growth>=80: {count}")
