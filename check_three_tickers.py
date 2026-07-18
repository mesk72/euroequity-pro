import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ticker in ["AAPL", "MSFT", "NVDA"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,price,eps_ntm_dcf,implied_growth,updated_at","ticker":f"eq.{ticker}","exchange":"eq.US"})
    print(f"{ticker} (fundamentals):", r.json())

    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":"eq.US","order":"date.desc","limit":"3"})
    print(f"{ticker} (prices_eod ultimi 3):", r2.json())
    print()
