import os, requests
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def fetch_all(table, params_extra):
    all_rows = []
    offset = 0
    while True:
        p = {**params_extra, "limit": "1000", "offset": str(offset)}
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_r, params=p)
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_rows.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return all_rows

# sector vive in stocks, mkt_cap + implied_growth_10y in fundamentals
stocks_data = fetch_all("stocks", {"select":"ticker,exchange,sector","exchange":"eq.US"})
fund_data = fetch_all("fundamentals", {"select":"ticker,exchange,mkt_cap,implied_growth_10y",
    "exchange":"eq.US","mkt_cap":"not.is.null","implied_growth_10y":"not.is.null"})

sector_map = {s["ticker"]: s.get("sector") or "Unknown" for s in stocks_data}

groups = defaultdict(lambda: {"wsum":0.0, "capsum":0.0, "count":0})
for f in fund_data:
    sec = sector_map.get(f["ticker"])
    if not sec: continue
    cap = f["mkt_cap"]
    ig = f["implied_growth_10y"]
    groups[sec]["wsum"] += ig * cap
    groups[sec]["capsum"] += cap
    groups[sec]["count"] += 1

results = []
for sec, g in groups.items():
    if g["capsum"] > 0:
        results.append((sec, g["wsum"]/g["capsum"]*100, g["count"], g["capsum"]/1000))

results.sort(key=lambda x: -x[3])  # ordina per mkt cap totale del settore

print(f"{'Settore':<28} {'Implied Growth':>15} {'Titoli':>8} {'Mkt Cap ($B)':>14}")
print("-"*68)
for sec, ig, count, cap in results:
    print(f"{sec:<28} {ig:>14.2f}% {count:>8} {cap:>13.1f}")
