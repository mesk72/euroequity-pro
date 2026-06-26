import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_3D     = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

print("=== FTSE MIB — formati alternativi ===")
for lt in ["FTSEMIB.MI", "FTMIB.INDX", "FTSEMIB.INDX", "MIB.MI", "IT40.INDX"]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_3D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  ✅ {lt}: date={last.get('date')} close={last.get('close')}")
    else:
        print(f"  ❌ {lt}: vuoto")

print()
print("=== FTSE 100 — formati alternativi ===")
for lt in ["FTSE.INDX", "UKX.INDX", "FTSE100.INDX", "^FTSE.INDX", "FTSE.LSE"]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_3D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  ✅ {lt}: date={last.get('date')} close={last.get('close')}")
    else:
        print(f"  ❌ {lt}: vuoto")
