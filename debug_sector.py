import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Prezzo attuale (ultimo disponibile)
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.GOOGL","exchange":"eq.US","order":"date.desc","limit":"1"})
latest = r.json()
print("Ultimo prezzo:", latest)

if latest:
    today = latest[0]["date"]
    today_price = latest[0]["adj_close"]

    for label, days in [("1 settimana",7), ("1 mese",30), ("6 mesi",182), ("12 mesi",365)]:
        target_date = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")
        # Prendo il prezzo piu' vicino (uguale o precedente) alla data target
        r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":"eq.GOOGL","exchange":"eq.US",
                     "date":f"lte.{target_date}","order":"date.desc","limit":"3"})
        near = r2.json()
        print(f"\n{label} (target {target_date}):")
        for row in near:
            perf = (today_price / row["adj_close"] - 1) * 100
            print(f"  {row['date']}: {row['adj_close']} -> perf da qui a oggi = {perf:.2f}%")
