import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# 1) Check su titoli noti - data più recente REALE in prices_eod (non latest_prices, non daily_log)
print("=== Verifica diretta prices_eod per titoli noti ===")
for tk, ex in [("ASML","AS"), ("SAP","XETRA"), ("MC","PA"), ("AAPL","US"), ("MSFT","US"), ("SHOP","TSX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}.{ex}: {r.json()}")

# 2) Distribuzione reale delle date su TUTTO l'universo EU e NA, via latest_prices (che ora sappiamo puo' essere disallineata da prices_eod, quindi la confrontiamo)
print("\n=== Distribuzione date in latest_prices (cache) ===")
for label, exchanges in [("EU", ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
                          ("NA", ["US","TSX"])]:
    all_dates = []
    for ex in exchanges:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
            params={"select":"price_date","exchange":f"eq.{ex}","limit":"3000"})
        rows = r.json()
        all_dates.extend(row["price_date"] for row in rows)
    c = Counter(all_dates)
    print(f"{label}: totale {len(all_dates)} righe, distribuzione date: {dict(c.most_common(5))}")
