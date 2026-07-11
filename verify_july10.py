import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1"})
print("US universo totale:", r1.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1"})
print("US al 10 luglio esatto (count):", r2.headers.get("content-range"))

r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","date":"gte.2026-07-09","limit":"1"})
print("US al 9 luglio o piu' recente:", r3.headers.get("content-range"))
