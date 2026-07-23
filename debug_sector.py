import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company,in_universe","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL in stocks:", r1.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/top500_universe", headers=headers_r,
    params={"select":"*","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL in top500_universe:", r2.json())

r3 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,mkt_cap,value_score,growth_score,combined_rank","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL in fundamentals:", r3.json())
