import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

INDICES = [
    ("FTSEMIB.MI",   "FTSE MIB"),
    ("SSMI.INDX",    "SMI"),
    ("ATX.INDX",     "ATX"),
    ("GDAXI.INDX",   "DAX"),
    ("FCHI.INDX",    "CAC 40"),
    ("FTSE.INDX",    "FTSE 100"),
    ("STOXX50E.INDX","Euro Stoxx 50"),
]

for lt, name in INDICES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        print(f"  {name} ({lt}): HTTP {r.status_code}")
        continue
    data = r.json()
    if not isinstance(data, list) or not data:
        print(f"  {name} ({lt}): vuoto")
        continue
    data = sorted(data, key=lambda x: x["date"])
    for row in data[-3:]:
        print(f"  {name} ({lt}): date={row.get('date')} open={row.get('open')} close={row.get('close')} adj={row.get('adjusted_close')}")
    print()
