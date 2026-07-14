import os, requests, statistics
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

all_caps = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap","exchange":"eq.US","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe and d.get("mkt_cap") is not None:
            all_caps.append(d["mkt_cap"])
    offset += 1000
    if len(batch) < 1000: break

all_caps.sort(reverse=True)
top500 = all_caps[:500]
print(f"Titoli totali con mkt_cap: {len(all_caps)}")
print(f"Top 500 - max: {top500[0]:.2f}B, min: {top500[-1]:.2f}B")
print(f"Mediana top 500: {statistics.median(top500):.2f}B")
print(f"Media top 500: {statistics.mean(top500):.2f}B")
