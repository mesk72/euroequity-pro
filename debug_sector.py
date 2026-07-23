import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== PREZZI ===")
for ticker, exchange in [("AAPL","US"), ("7203","TSE"), ("SAP","XETRA")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    print(f"{ticker}.{exchange}:", r.json())

print("\n=== NOTIZIE ===")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers={**headers_r,"Prefer":"count=exact"}, params={"select":"ticker","limit":"1"})
print("Righe totali news_cache:", r2.headers.get("content-range"))
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker,fetched_at","order":"fetched_at.desc","limit":"3"})
print("Ultime righe inserite:", r3.json())
