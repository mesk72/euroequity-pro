import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

def get_fundamentals():
    all_data = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,value_score,growth_score","exchange":"eq.US","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_data.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return all_data

all_fund = get_fundamentals()

def report(label, filtered):
    filtered_in_universe = [q for q in filtered if q["ticker"] in sector_by_ticker]
    total = len(filtered_in_universe)
    print(f"\n=== {label}: {total} titoli ===")
    sector_counts = Counter(sector_by_ticker[q["ticker"]] for q in filtered_in_universe)
    for sector, count in sector_counts.most_common():
        pct = 100 * count / total if total else 0
        print(f"  {sector}: {count} titoli = {pct:.2f}%")

value_filtered = [d for d in all_fund if (d.get("value_score") or 0) >= 80 and (d.get("growth_score") or 0) >= 30]
growth_filtered = [d for d in all_fund if (d.get("growth_score") or 0) >= 80]

report("VALUE (Value>=80 e Growth>=30)", value_filtered)
report("GROWTH (Growth>=80)", growth_filtered)
