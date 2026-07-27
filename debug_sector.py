import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

t0 = time.time()
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select": "date", "exchange": "eq.US", "order": "date.desc", "limit": "1"}, timeout=30)
elapsed = time.time() - t0
print(f"Status: {r.status_code}, tempo: {elapsed:.2f}s")
print("Risposta:", r.text[:300])
