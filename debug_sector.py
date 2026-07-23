import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"*","ticker":"eq.9984","exchange":"eq.TSE"})
print("stocks:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,change1d,value_score,growth_score,combined_rank,mom1w,mom1m","ticker":"eq.9984","exchange":"eq.TSE"})
print("\nfundamentals completo:", r2.json())
