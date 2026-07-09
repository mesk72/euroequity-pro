import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","beta":"not.is.null","limit":"1"})
print("Beta popolato US:", r1.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/macro_rates", headers=headers_r,
    params={"select":"*","region":"eq.US","order":"updated_at.desc","limit":"3"})
print("macro_rates ultimi 3:", r2.json())
