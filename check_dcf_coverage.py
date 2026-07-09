import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","in_universe":"eq.true","exchange":"eq.US","limit":"1"})
print("Universo US totale:", r1.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","eps_ntm_dcf":"not.is.null","limit":"1"})
print("Con eps_ntm_dcf popolato:", r2.headers.get("content-range"))
