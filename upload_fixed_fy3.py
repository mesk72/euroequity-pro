import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "text/csv", "x-upsert": "true"}
with open("fiscal_year_end_merged3.csv", "rb") as f:
    content = f.read()
r = requests.put(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers, data=content)
print(f"HTTP {r.status_code}: {r.text[:300]}")
