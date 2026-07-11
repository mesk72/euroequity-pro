import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_count,
    params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1"}, timeout=30)
print(f"HTTP {r.status_code}")
print("Content-Range:", r.headers.get("content-range"))
print("Body:", r.text[:200])
