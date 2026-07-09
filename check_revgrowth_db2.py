import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for t, ex in [("D05","SGX"),("700","SEHK"),("BHP","ASX"),("7203","TSE")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,rev_growth,eps_growth,eps_fy0,eps_fy1","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    print(f"{t}.{ex}: {r.json()}")
