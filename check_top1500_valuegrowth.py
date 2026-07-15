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

qualifying = [d for d in top1500
              if d.get("value_score") is not None and d.get("growth_score") is not None
              and d["value_score"] >= 80 and d["growth_score"] >= 80]

total = len(qualifying)
print(f"Titoli con Value>=80 E Growth>=80 (nei top 1500 per market cap): {total}")

if total > 0:
    sector_counts = Counter(universe[d["ticker"]] for d in qualifying)
    for sector, count in sector_counts.most_common():
        pct = 100 * count / total
        print(f"  {sector}: {count} titoli = {pct:.2f}%")
