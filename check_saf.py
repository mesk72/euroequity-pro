import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"price,mom1m,mom1w","ticker":"eq.SAF","exchange":"eq.PA"})
print("SAF fundamentals:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.SAF","exchange":"eq.PA","order":"date.desc","limit":"45"})
rows = r2.json()
print(f"\nUltimi prezzi (piu' recenti in cima):")
for row in rows[:10]:
    print(f"  {row}")

latest_date = rows[0]["date"]
latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
target_30 = latest_dt - timedelta(days=30)
target_31 = latest_dt - timedelta(days=31)
print(f"\nData piu' recente: {latest_date}")
print(f"Target 30 giorni fa: {target_30.strftime('%Y-%m-%d')}")
print(f"Target 31 giorni fa: {target_31.strftime('%Y-%m-%d')}")

prices_by_date = {row["date"]: row["adj_close"] for row in rows}
def nearest(target, tol=6):
    best=None; bd=None
    for d,p in prices_by_date.items():
        dt = datetime.strptime(d, "%Y-%m-%d")
        diff = abs((dt-target).days)
        if diff<=tol and (bd is None or diff<bd):
            best=p; bd=diff
    return best

p30 = nearest(target_30)
p31 = nearest(target_31)
print(f"\nPrezzo trovato vicino a target 30gg: {p30}")
print(f"Prezzo trovato vicino a target 31gg: {p31}")
latest_price = rows[0]["adj_close"]
if p30: print(f"mom1m con finestra 30gg: {(latest_price/p30-1)*100:.2f}%")
if p31: print(f"mom1m con finestra 31gg: {(latest_price/p31-1)*100:.2f}%")
