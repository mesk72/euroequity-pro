import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== REVERSE EARNINGS MODEL (implied_growth_10y) ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,implied_growth_10y,beta,ke","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL:", r.json())

print("\n=== PREZZI PER MERCATO ===")
for ticker, exchange in [("AAPL","US"), ("SAP","XETRA"), ("7203","TSE")]:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    print(f"{ticker}.{exchange}:", r2.json())
