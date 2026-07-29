import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for col in ["company_name", "company"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,in_universe", col: "ilike.*roche*"})
    print(f"stocks (ilike {col}=roche):", r.json())

for tk in ["ROG","RO","RHHBY","RHHVF"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,company_name,in_universe","ticker":f"eq.{tk}"})
    print(f"ticker={tk}:", r.json())
