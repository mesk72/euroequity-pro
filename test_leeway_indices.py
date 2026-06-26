import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

# Test 285A.TSE e altri JP
print("=== GIAPPONE ===")
for lt in ["285A.TSE", "7203.TSE", "9984.TSE"]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        data = sorted(data, key=lambda x: x["date"])
        last = data[-1]
        print(f"  {lt}: ultima data={last['date']} close={last.get('close')}")
    else:
        print(f"  {lt}: HTTP {r.status_code} — vuoto o errore")

print()
print("=== AUSTRALIA (nuovo .AU) ===")
for lt in ["BHP.AU", "CBA.AU", "CSL.AU"]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        data = sorted(data, key=lambda x: x["date"])
        last = data[-1]
        print(f"  {lt}: ultima data={last['date']} close={last.get('close')}")
    else:
        print(f"  {lt}: HTTP {r.status_code} — vuoto o errore")
