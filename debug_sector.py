import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","company":"ilike.*rolls*royce*"})
print("Rolls-Royce varianti:", r1.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","company":"ilike.*alphabet*"})
print("Alphabet varianti:", r2.json())
