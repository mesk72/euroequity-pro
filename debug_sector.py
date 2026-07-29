import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

stuck = ['1551','2362','754','2596','247','2558','1788']
for t in stuck:
    ytk = t.zfill(4) + ".HK"
    print(f"\n=== {t} -> {ytk} ===")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{t}","exchange":"eq.SEHK","order":"date.desc","limit":"3"})
    print("DB:", r.json())
    try:
        df = yf.download(ytk, period="5d", interval="1d", auto_adjust=True, progress=False)
        print("Yahoo:", df["Close"].tail(3).to_dict() if not df.empty else "VUOTO su Yahoo")
    except Exception as e:
        print("Yahoo errore:", e)

    # controlla anche se il ticker esiste nella tabella stocks con dati corretti
    rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,in_universe,yahoo_ticker","ticker":f"eq.{t}","exchange":"eq.SEHK"})
    print("stocks:", rs.json())
