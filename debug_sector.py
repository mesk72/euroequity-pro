import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
    params={"select":"*","ticker":"eq.WES","exchange":"eq.ASX"})
print("latest_prices WES:", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,price,mom1w,mom1m,mom6m,mom12m","ticker":"eq.WES","exchange":"eq.ASX"})
print("fundamentals WES:", r2.json())
