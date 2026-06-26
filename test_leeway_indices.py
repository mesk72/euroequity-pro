import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("TODAY:", TODAY)
print()

# Simulo esattamente quello che fa daily_apac per 285A
ticker   = "285A"
exchange = "TSE"
lt       = ticker + ".TSE"

# Step 1: leggi ultima data dal DB
r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
    params={"select": "date", "ticker": "eq." + ticker,
            "exchange": "eq." + exchange, "order": "date.desc", "limit": "1"})
row = r.json()
last = row[0]["date"] if isinstance(row, list) and row else "2021-01-01"
print(f"Ultima data nel DB per {ticker}: {last}")
print(f"last >= TODAY: {last >= TODAY} → {'SKIP' if last >= TODAY else 'SCARICA'}")

if last >= TODAY:
    print("SKIP — già aggiornato")
else:
    start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"start_dt: {start_dt}")
    
    # Step 2: scarica da Leeway
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + start_dt + "&to=" + TODAY
    print(f"URL: {url}")
    resp = requests.get(url, timeout=15)
    print(f"HTTP: {resp.status_code}")
    data_l = resp.json() if resp.status_code == 200 else []
    print(f"Righe restituite: {len(data_l) if isinstance(data_l, list) else 'ERR'}")
    if isinstance(data_l, list) and data_l:
        for row2 in data_l:
            print(f"  date={row2.get('date')} close={row2.get('close')} adj={row2.get('adjusted_close')}")
