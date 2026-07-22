import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers={**headers_r,"Prefer":"count=exact"},
    params={"select":"ticker","limit":"1"})
print("Righe attuali (prima di qualunque azione):", r2.headers.get("content-range"))
