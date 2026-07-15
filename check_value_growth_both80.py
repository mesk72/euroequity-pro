import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

universe = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,sector","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch:
        universe[s["ticker"]] = s.get("sector") or "Other"
    offset += 1000
    if len(batch) < 1000: break

qualifying = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","value_score":"gte.80","growth_score":"gte.80","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe:
            qualifying.append(d["ticker"])
    offset += 1000
    if len(batch) < 1000: break

total = len(qualifying)
print(f"Totale titoli: {total}")
sector_counts = Counter(universe[t] for t in qualifying)
for sector, count in sector_counts.most_common():
    pct = 100 * count / total
    print(f"  {sector}: {count} titoli = {pct:.2f}%")
