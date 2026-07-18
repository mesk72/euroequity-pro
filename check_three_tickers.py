import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker in ["005930", "005930.KS", "SSNLF"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mom1m,price,updated_at","ticker":f"eq.{ticker}"})
    d = r.json()
    if d:
        print(f"{ticker}:", d)

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company_name","company_name":"ilike.*samsung*","limit":"10"})
print("\nRicerca per nome:", r2.json())
