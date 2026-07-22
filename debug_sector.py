import os, requests, datetime
from dateutil.relativedelta import relativedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ticker, exchange = "AAPL", "US"

# Prezzo storico completo, ordinato desc
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
             "order":"date.desc","limit":"1600"})
prices = r.json()
data = [{"date": p["date"], "close": p["adj_close"]} for p in prices]

last_px = data[0]["close"]
last_date = datetime.date.fromisoformat(data[0]["date"])
print(f"Prezzo piu' recente: {last_px} al {last_date}")

# mom1w: 4 giorni di trading indietro
ref_1w = data[4]
mom1w_expected = round(last_px / ref_1w["close"] - 1, 6)
print(f"\nmom1w atteso: rif={ref_1w['date']} prezzo={ref_1w['close']} -> {mom1w_expected}")

# mom1m/6m/12m: calendario+1gg, primo disponibile
def mom_new_months(months):
    target = last_date - relativedelta(months=months)
    target_plus1 = target + datetime.timedelta(days=1)
    candidates = [p for p in data if p["date"] >= target_plus1.isoformat()]
    ref = min(candidates, key=lambda p: p["date"])
    val = round(last_px / ref["close"] - 1, 6)
    return ref, val

for m in [1, 6, 12]:
    ref, val = mom_new_months(m)
    print(f"mom{m}m atteso: rif={ref['date']} prezzo={ref['close']} -> {val}")

# Confronto col valore reale nel database
rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"mom1w,mom1m,mom6m,mom12m","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
real = rf.json()[0] if rf.json() else {}
print(f"\nValori REALI nel database: {real}")
