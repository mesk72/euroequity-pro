import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/top500_universe", headers=headers_r, params={"select":"ticker","limit":"1"})
print("Righe in top500_universe:", r.headers.get("content-range"))
print("Status:", r.status_code)
