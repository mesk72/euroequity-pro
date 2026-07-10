import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.delete(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_us_latest.csv", headers=headers)
print(f"HTTP {r.status_code}: {r.text[:200]}")
