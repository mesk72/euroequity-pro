import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

CANDIDATES = [
    # Roche — formati alternativi
    ("ROG.SW",    "Roche .SW"),
    ("ROG.SWX",   "Roche .SWX"),
    ("ROG.XSWX",  "Roche .XSWX"),
    ("RO.SW",     "Roche RO.SW"),
    ("ROG.CH",    "Roche .CH"),
    # Nestle verifica
    ("NESN.SW",   "Nestle .SW"),
    ("NESN.SWX",  "Nestle .SWX"),
    # Irlanda — formati alternativi
    ("CRH.IR",    "CRH .IR"),
    ("CRH.ISE",   "CRH .ISE"),
    ("CRH.IE",    "CRH .IE"),
    ("AIB.IR",    "AIB .IR"),
    ("AIB.ISE",   "AIB .ISE"),
    ("AIB.IE",    "AIB .IE"),
]

for lt, name in CANDIDATES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {name} ({lt}): {last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {name} ({lt}): vuoto")
