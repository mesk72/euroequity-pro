import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,mom1w,mom1m,mom6m,mom12m,value_score,growth_score,combined_rank,rank_mom6_adj,rank_mom12_adj","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA completo:", r.json())
