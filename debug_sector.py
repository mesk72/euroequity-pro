import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ex in ["XETRA", "TSE", "US"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers={**headers_r,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":f"eq.{ex}","combined_rank":"not.is.null","limit":"1"})
    print(f"{ex}: quanti con Best Score = {r.headers.get('content-range')}")
