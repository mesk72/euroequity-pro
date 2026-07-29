import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for tk, ex, ytk in [("1COV","XETRA","1COV.DE"), ("NUVL","US","NUVL"), ("XOMA","US","XOMA"), ("OLPX","US","OLPX")]:
    print(f"\n=== {tk}.{ex} ===")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"3"})
    print("prices_eod (fonte grezza):", r.json())
    rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,in_universe,yahoo_ticker,company_name","ticker":f"eq.{tk}","exchange":f"eq.{ex}"})
    print("stocks:", rs.json())
    try:
        df = yf.download(ytk, period="10d", interval="1d", auto_adjust=True, progress=False)
        print("Yahoo diretto:", df["Close"].tail(5).to_dict() if not df.empty else "VUOTO")
    except Exception as e:
        print("Yahoo errore:", e)
