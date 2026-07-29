import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

exchanges = ["ASX","TSE","SEHK","KRX","SGX"]
stale_all = {}
for ex in exchanges:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
        params={"select":"ticker,price_date","exchange":f"eq.{ex}","limit":"3000"})
    rows = r.json()
    if not rows:
        print(f"{ex}: nessun dato in latest_prices")
        continue
    dates = Counter(row["price_date"] for row in rows)
    top_date = dates.most_common(1)[0][0]
    stale = [row["ticker"] for row in rows if row["price_date"] != top_date]
    print(f"{ex}: {len(rows)} titoli, data prevalente={top_date}, distribuzione date={dict(dates)}")
    if stale:
        print(f"  -> {len(stale)} indietro: {stale[:20]}")
        stale_all[ex] = stale

import json
with open("stale_list.json","w") as f:
    json.dump(stale_all, f)
print("\nSTALE_ALL:", stale_all)
