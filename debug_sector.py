import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# 1) Cosa dice Yahoo ADESSO per WES.AX
print("=== YAHOO (yfinance) WES.AX ultimi 10 giorni ===")
try:
    df = yf.download("WES.AX", period="10d", interval="1d", auto_adjust=True, progress=False)
    print(df.tail(10))
except Exception as e:
    print("ERRORE yfinance:", e)

# 2) Cosa c'e' nel nostro DB per WES su ASX, ultimi giorni
print("\n=== DB prices_eod WES/ASX ultimi 10 record ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.WES","exchange":"eq.ASX","order":"date.desc","limit":"10"})
print(r.json())

# 3) Controlla se WES appare in un secondo ticker/exchange diverso per errore
print("\n=== stocks table: eventuali record WES ===")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company_name,yahoo_ticker,in_universe","ticker":"eq.WES"})
print(r2.json())
