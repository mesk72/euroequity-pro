import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_up,
    params={"ticker":"eq.A000660","exchange":"eq.KRX","adj_close":"eq.999999.9999"})
print(f"Delete HTTP {r.status_code}: {r.text[:200]}")
