import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"ilike.SIMO*"})
print("Ticker che iniziano con SIMO (qualsiasi borsa):", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","company":"ilike.*Silicon Motion*"})
print("\nAziende con 'Silicon Motion' nel nome:", r2.json())
