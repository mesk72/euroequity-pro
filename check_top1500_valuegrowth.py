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

all_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,value_score,growth_score","exchange":"eq.US","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe and d.get("mkt_cap") is not None:
            all_data.append(d)
    offset += 1000
    if len(batch) < 1000: break

all_data.sort(key=lambda x: -x["mkt_cap"])
top1500 = all_data[:1500]
print(f"Titoli nel top 1500 per market cap: {len(top1500)}")

count = sum(1 for d in top1500
            if d.get("value_score") is not None and d.get("growth_score") is not None
            and d["value_score"] >= 80 and d["growth_score"] >= 30)
print(f"Con Value>=80 E Growth>=30: {count}")
