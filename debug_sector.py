import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== YAHOO BHP.AX ultimi 8 giorni ===")
df = yf.download("BHP.AX", period="10d", interval="1d", auto_adjust=True, progress=False)
print(df.tail(8))

print("\n=== DB prices_eod BHP/ASX ultimi 8 record ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.BHP","exchange":"eq.ASX","order":"date.desc","limit":"8"})
print(r.json())

print("\n=== latest_prices BHP ===")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
    params={"select":"*","ticker":"eq.BHP","exchange":"eq.ASX"})
print(r2.json())
