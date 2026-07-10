import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for t, ex in [("8309","TSE"),("J36","SGX"),("700","SEHK")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,eps_growth,rev_growth","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    print(f"{t}.{ex}: {r.json()}")
