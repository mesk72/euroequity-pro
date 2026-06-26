import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_3D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

# Test 3 indici problematici
TEST_INDICES = [
    ("SSMI.INDX",   "SMI"),
    ("ATX.INDX",    "ATX"),
    ("FTSEMIB.MI",  "FTSE MIB"),
    ("GDAXI.INDX",  "DAX"),
]

for lt, name in TEST_INDICES:
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_3D}&to={TODAY}"
    r = requests.get(url, timeout=10)
    print(f"\n{name} ({lt}) — HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            for row in data:
                print(f"  date={row.get('date')} open={row.get('open')} high={row.get('high')} low={row.get('low')} close={row.get('close')} adj={row.get('adjusted_close')} volume={row.get('volume')}")
        else:
            print(f"  Response: {data}")
    else:
        print(f"  Error: {r.text[:200]}")
