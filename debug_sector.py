import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,growth_score,combined_rank,value_score,eps_growth,rev_growth,mom6m,mom1w,mom12m,mom1m,updated_at","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA fundamentals ORA:", r.json())
