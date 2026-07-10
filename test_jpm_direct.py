import os, requests
from datetime import datetime, timedelta
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
to_d = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now()-timedelta(days=10)).strftime("%Y-%m-%d")
for t in ["JPM", "AAPL"]:
    url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{t}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    r = requests.get(url, timeout=20)
    print(f"{t}: HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and data:
            for row in sorted(data, key=lambda x: x.get("date",""))[-5:]:
                print(f"   {row}")
        else:
            print("   risposta vuota")
    else:
        print(f"   {r.text[:200]}")
