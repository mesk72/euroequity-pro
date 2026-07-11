import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
samples = [("JPM","US"),("AAPL","US"),("ASML","AS"),("SAP","XETRA"),("VOD","LSE"),
           ("7203","TSE"),("700","SEHK"),("BHP","ASX"),("A005930","KRX"),("D05","SGX")]
for t, ex in samples:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{t}.{ex}: {r.json()}")
