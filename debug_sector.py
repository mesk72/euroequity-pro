import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

samples = [("AAPL","US"), ("SAP","XETRA"), ("7203","TSE")]

for ticker, exchange in samples:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                 "order":"date.desc","limit":"40"})
    rows = sorted(r.json(), key=lambda x: x["date"])
    print(f"\n=== {ticker}.{exchange} — ultimi 40 giorni ===")
    prev = None
    for row in rows:
        pct = None
        if prev is not None and prev != 0:
            pct = round((row["adj_close"]/prev - 1)*100, 2)
        flag = "  <-- SALTO SOSPETTO" if pct is not None and abs(pct) > 8 else ""
        print(f"  {row['date']}  {row['adj_close']}  {pct}%{flag}")
        prev = row["adj_close"]
