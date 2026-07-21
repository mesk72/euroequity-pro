import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company,in_universe","ticker":"eq.IBM","exchange":"eq.US"})
print("IBM in stocks:", r1.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,mkt_cap","ticker":"eq.IBM","exchange":"eq.US"})
print("IBM in fundamentals:", r2.json())

# Quanti titoli hanno mkt_cap maggiore di IBM (per capire la sua vera posizione)
ibm_cap = r2.json()[0].get("mkt_cap") if r2.json() else None
print(f"\nMkt cap IBM: {ibm_cap}")
