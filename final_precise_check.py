import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.NVDA","exchange":"eq.US"})
data = r.json()[0]
print("Valori GREZZI nel database, esattamente come sono salvati:")
for k in ["change1d","mom1w","mom1m","mom6m","mom12m"]:
    v = data.get(k)
    print(f"  {k}: {v!r}  ->  se il frontend fa *100: {v*100 if v is not None else None}")
