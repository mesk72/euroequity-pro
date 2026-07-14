import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

universe = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,company","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch:
        universe[s["ticker"]] = s.get("company","?")
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
            all_caps.append((d["ticker"], universe[d["ticker"]], d["mkt_cap"]))
    offset += 1000
    if len(batch) < 1000: break

all_caps.sort(key=lambda x: -x[2])
print("Top 20 per market cap (grezzo dal database):")
for t, c, m in all_caps[:20]:
    print(f"  {t} ({c[:35]}): {m:,.2f}")
