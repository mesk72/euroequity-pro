import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1000","offset":"0"}, timeout=30)
print(f"HTTP status: {r.status_code}")
print(f"Risposta (primi 500 char): {r.text[:500]}")
