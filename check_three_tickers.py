import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Prova KRX con ticker noto Samsung Electronics = 005930
for ticker in ["005930"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"*","ticker":f"eq.{ticker}","exchange":"eq.KRX"})
    print(f"{ticker} KRX fundamentals:", r.json())
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":"eq.KRX","order":"date.desc","limit":"25"})
    print(f"{ticker} prezzi ultimi 25gg:", r2.json())
