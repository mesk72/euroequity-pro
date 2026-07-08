import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"*","ticker":"eq.4974","exchange":"eq.TSE"})
print("Riga stocks:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date","ticker":"eq.4974","exchange":"eq.TSE","order":"date.desc","limit":"3"})
print("Ultimi prezzi in DB:", r2.json())

to_d = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
url = f"https://api.leeway.tech/api/v1/public/historicalquotes/4974.TSE?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
resp = requests.get(url, timeout=20)
print(f"Leeway 4974.TSE: HTTP {resp.status_code}")
print("Body:", resp.text[:400])
