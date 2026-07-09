import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
to_d = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now()-timedelta(days=15)).strftime("%Y-%m-%d")
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","in_universe":"eq.true","exchange":"eq.US","limit":"5"})
tickers = [s["ticker"] for s in r.json()]
for t in tickers:
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"1"})
    d = rp.json()
    db_date = d[0]["date"] if isinstance(d,list) and d else "VUOTO"
    url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{t}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        max_d = max(d2["date"] for d2 in data) if isinstance(data,list) and data else "vuoto"
    else:
        max_d = f"HTTP {resp.status_code}"
    print(f"{t}.US: DB={db_date}  Leeway diretto={max_d}")
