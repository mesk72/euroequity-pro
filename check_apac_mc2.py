import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
samples = [("7203","TSE"),("700","SEHK"),("BHP","ASX"),("A005930","KRX"),("D05","SGX")]
for t, ex in samples:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mkt_cap","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    print(f"{t}.{ex}: {r.json()}")
