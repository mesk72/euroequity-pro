import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r, params={"select":"ticker","limit":"1"})
print("Righe totali in latest_prices:", r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"*","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL in latest_prices:", r2.json())

r3 = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"*","ticker":"eq.9984","exchange":"eq.TSE"})
print("9984 SoftBank in latest_prices:", r3.json())
