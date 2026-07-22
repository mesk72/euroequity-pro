import os, sys, subprocess
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dateutil", "--break-system-packages", "-q"])
    from dateutil.relativedelta import relativedelta
import requests, datetime

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ticker, exchange = "AAPL", "US"

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
             "order":"date.desc","limit":"1600"})
prices = r.json()
data = [{"date": p["date"], "close": p["adj_close"]} for p in prices]

last_px = data[0]["close"]
last_date = datetime.date.fromisoformat(data[0]["date"])
print(f"Prezzo piu' recente: {last_px} al {last_date}")

ref_1w = data[4]
mom1w_expected = round(last_px / ref_1w["close"] - 1, 6)
print(f"\nmom1w atteso: rif={ref_1w['date']} prezzo={ref_1w['close']} -> {mom1w_expected}")

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

rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"mom1w,mom1m,mom6m,mom12m","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
real = rf.json()[0] if rf.json() else {}
print(f"\nValori REALI nel database: {real}")
