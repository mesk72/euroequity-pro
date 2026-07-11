import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.JPM","exchange":"eq.US","order":"date.desc","limit":"5"})
print("JPM ultimi 5:", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"5"})
print("Query eq.2026-07-10 (primi 5 risultati):", r2.json())
print("Status:", r2.status_code)
