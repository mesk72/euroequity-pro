import os, requests, datetime
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

for t, ex in [("7203","TSE"),("700","SEHK"),("BHP","ASX"),("A005930","KRX"),("D05","SGX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{t}.{ex}: {r.json()}")

for ex in ["ASX","KRX","SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1"})
    print(f"Universo {ex}:", r.headers.get("content-range"))
