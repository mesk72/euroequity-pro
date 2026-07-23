import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker, exchange in [("AAPL","US"), ("7203","TSE"), ("SAP","XETRA")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    print(f"{ticker}.{exchange} ultima data prezzo:", r.json())
