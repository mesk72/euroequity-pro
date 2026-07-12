import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type":"application/json"}
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"eq.0E2B"})
print("Trovato:", r.json())

resp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
    params={"ticker":"eq.0E2B","exchange":"eq.LSE"}, json={"in_universe": False})
print(f"Esclusione: HTTP {resp.status_code}")
