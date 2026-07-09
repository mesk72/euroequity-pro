import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for t,ex in [("JPM","US"),("AAPL","US"),("MSFT","US"),("TSLA","US")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{t}.{ex}: {r.json()}")
