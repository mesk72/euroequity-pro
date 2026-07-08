import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
for exch in ["US","TSX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"1"})
    print(f"{exch}: {r.headers.get('content-range')}")
