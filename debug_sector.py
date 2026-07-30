import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/sector_quintile_partials", headers=headers_r | {"Prefer":"count=exact"}, params={"select":"exchange","limit":"1"})
print("Righe totali:", r.headers.get("content-range"))
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/sector_quintile_partials", headers=headers_r, params={"select":"exchange","limit":"1000"})
exchanges = sorted(set(row["exchange"] for row in r2.json()))
print("Exchange presenti:", exchanges)
