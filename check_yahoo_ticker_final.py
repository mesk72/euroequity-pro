import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","yahoo_ticker":"not.is.null","limit":"1"})
print("yahoo_ticker US:", r1.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,website","exchange":"eq.US","in_universe":"eq.true","yahoo_ticker":"is.null","limit":"15"})
print("Esempi senza yahoo_ticker:", r2.json())
