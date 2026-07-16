import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker in ["NVDA", "JNJ"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,rank_mom6_adj,rank_mom12_adj,mom6m,mom12m,mom1w,mom1m","ticker":f"eq.{ticker}","exchange":"eq.US"})
    print(f"{ticker}:", r.json())
