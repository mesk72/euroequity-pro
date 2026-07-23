import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers={**headers_r,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","combined_rank":"not.is.null","limit":"1"})
print("US con Best Score:", r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,value_score,growth_score,combined_rank","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL:", r2.json())
