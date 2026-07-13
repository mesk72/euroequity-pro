import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Universo US in_universe=true
universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,sector","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch:
        universe.add((s["ticker"], s.get("sector") or "Other"))
    offset += 1000
    if len(batch) < 1000: break
sector_by_ticker = dict(universe)
print(f"Universo US: {len(sector_by_ticker)} titoli")

# Fundamentals con combined_rank >= 80
qualifying = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,combined_rank","exchange":"eq.US","combined_rank":"gte.80","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    qualifying.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

qualifying_in_universe = [q for q in qualifying if q["ticker"] in sector_by_ticker]
print(f"Titoli con Best Score >= 80 (in universo): {len(qualifying_in_universe)}")

sector_counts = Counter(sector_by_ticker[q["ticker"]] for q in qualifying_in_universe)
total = len(qualifying_in_universe)
print(f"\nRipartizione settoriale (equal-weight, {total} titoli):")
for sector, count in sector_counts.most_common():
    pct = 100 * count / total
    print(f"  {sector}: {count} titoli = {pct:.2f}%")
