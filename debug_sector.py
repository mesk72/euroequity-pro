import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"mom1w,mom1m,mom6m,mom12m","ticker":"eq.GOOGL","exchange":"eq.US"})
print("Valore salvato in fundamentals (usato da screener e pagina titolo):")
print(r.json())
