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
    if not rows: continue
    max_date = max(row["price_date"] for row in rows)
    stale = [row["ticker"] for row in rows if row["price_date"] != max_date]
    dates = Counter(row["price_date"] for row in rows)
    print(f"{ex}: {len(rows)} titoli, data PIU' RECENTE={max_date}, distribuzione={dict(dates)}")
    if stale:
        print(f"  -> {len(stale)} REALMENTE indietro rispetto a {max_date}: {stale[:25]}")
        stale_all[ex] = stale
print("\nTOTALE REALMENTE INDIETRO:", {k: len(v) for k, v in stale_all.items()})
