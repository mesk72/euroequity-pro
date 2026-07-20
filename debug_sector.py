import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,mkt_cap,sector","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA in stocks:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,mkt_cap","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA in fundamentals:", r2.json())

# Controlla quanti titoli IT US hanno mkt_cap valido in STOCKS
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,mkt_cap","exchange":"eq.US","sector":"eq.Information Technology","limit":"20"})
data3 = r3.json()
non_null = sum(1 for d in data3 if d.get("mkt_cap") is not None and d.get("mkt_cap") > 0)
print(f"\nCampione 20 titoli IT US - mkt_cap valido in STOCKS: {non_null}/20")
print("Esempi:", data3[:5])
