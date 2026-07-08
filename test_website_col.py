import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type":"application/json"}
r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"ticker":"eq.JPM","exchange":"eq.US"}, json={"website":"https://www.jpmorganchase.com"})
print("PATCH website test ->", r.status_code, r.text[:300])
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,website","ticker":"eq.JPM","exchange":"eq.US"})
print("verifica ->", r2.status_code, r2.json())
