import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/top500_universe", headers=headers_r, params={"select":"ticker","limit":"1"})
print("top500_universe:", r.status_code, r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/institutional_viewers", headers=headers_r, params={"select":"email","limit":"1"})
print("institutional_viewers:", r2.status_code, r2.headers.get("content-range"))
