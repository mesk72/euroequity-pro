import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","implied_growth_10y":"not.is.null","limit":"1"})
print("Titoli US con implied_growth_10y popolato:", r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"ticker,implied_growth_10y,beta,ke","ticker":"in.(AAPL,MSFT,NVDA)","exchange":"eq.US"})
print("Campione:", r2.json())
