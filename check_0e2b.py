import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}
r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker","ticker":"eq.0E2B","exchange":"eq.LSE","limit":"1"})
print("0E2B righe totali:", r.headers.get("content-range"))
# quanti ticker distinti LSE hanno >2000 righe (sospetti bloat)
r2 = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.LSE","in_universe":"eq.true","limit":"3"})
print("primi 3 LSE in_universe:", r2.json())
