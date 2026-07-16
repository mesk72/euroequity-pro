import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker, exchange in [("NVDA","US"), ("AAPL","US")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mom1w,mom1m,mom6m,mom12m,change1d,price,updated_at","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    print(f"{ticker}.{exchange}:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","order":"date.desc","limit":"10"})
print("\nNVDA ultimi 10 prezzi:")
for row in r2.json():
    print(f"  {row}")
