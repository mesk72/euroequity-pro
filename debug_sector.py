import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"ticker": "neq.___NONEXISTENT___"})
print("Delete status:", r.status_code)

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","limit":"3"})
print("Righe rimaste dopo delete:", r2.json())
