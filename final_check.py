import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","website":"not.is.null","limit":"1"})
print("Website US:", r1.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","beta":"not.is.null","limit":"1"})
print("Beta US:", r2.headers.get("content-range"))
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","eps_ntm_dcf":"not.is.null","limit":"1"})
print("DCF US:", r3.headers.get("content-range"))
r4 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.KRX","in_universe":"eq.true","website":"not.is.null","limit":"1"})
print("Website KRX:", r4.headers.get("content-range"))
r5 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.SGX","in_universe":"eq.true","website":"not.is.null","limit":"1"})
print("Website SGX:", r5.headers.get("content-range"))
