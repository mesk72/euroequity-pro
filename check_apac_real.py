import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

for exch in ["TSE","SEHK","ASX","KRX","SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"1"})
    print(f"{exch} in_universe: {r.headers.get('content-range')}")

print()
for t,ex in [("7203","TSE"),("0700","SEHK"),("BHP","ASX"),("005930","KRX"),("D05","SGX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{t}.{ex} ultima data prices_eod: {r.json()}")
