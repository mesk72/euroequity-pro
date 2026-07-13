import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=estimated"}
try:
    r = requests.head(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r, params={"select":"*"}, timeout=25)
    print("STATUS:", r.status_code)
    print("Content-Range:", r.headers.get("Content-Range"))
except Exception as e:
    print("ERRORE:", e)
