import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,implied_growth,beta_local,ke,eps_ntm_dcf","ticker":"eq.NVDA","exchange":"eq.US"})
print("Fundamentals NVDA dopo il fix:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","order":"date.desc","limit":"10"})
print("\nUltimi 10 prezzi in prices_eod:")
for p in r2.json():
    print(f"  {p}")
