import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker, exchange in [("AAPL","US"), ("SAP","XETRA"), ("7203","TSE")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.asc","limit":"1"})
    oldest = r.json()
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    newest = r2.json()
    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers={**headers_r,"Prefer":"count=exact"},
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    count = r3.headers.get("content-range","").split("/")[-1]
    print(f"{ticker}.{exchange}: piu' vecchia={oldest}, piu' recente={newest}, righe totali={count}")
