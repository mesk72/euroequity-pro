import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,change1d,mom1w,mom1m,mom6m,mom12m,value_score,growth_score,combined_rank","ticker":"eq.A005930","exchange":"eq.KRX"})
print("Samsung:", r.json())
