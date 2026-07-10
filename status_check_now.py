import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","eps_ntm_dcf":"not.is.null","limit":"1"})
print("DCF US:", r.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,eps_ntm_dcf","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL:", r2.json())
