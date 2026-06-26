import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_3D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

CANDIDATES = [
    # FTSE MIB
    ("FTSEMIB.MI",     "FTSE MIB"),
    ("MIB.MI",         "FTSE MIB alt"),
    ("FTSEMIB.XETRA",  "FTSE MIB alt2"),
    # FTSE 100
    ("FTSE.INDX",      "FTSE 100"),
    ("UKX.INDX",       "FTSE 100 alt1"),
    ("FTSE100.INDX",   "FTSE 100 alt2"),
    ("FTSE.LSE",       "FTSE 100 alt3"),
    ("ASX.LSE",        "FTSE 100 alt4"),
    # OMX Helsinki
    ("OMXHPI.INDX",    "OMX Helsinki"),
    ("OMXH25.INDX",    "OMX Helsinki alt1"),
    ("HEX.INDX",       "OMX Helsinki alt2"),
    # ISEQ
    ("ISEQ.INDX",      "ISEQ"),
    ("ISEQ20.INDX",    "ISEQ alt1"),
    ("ISEQX.INDX",     "ISEQ alt2"),
    # TSX
    ("OSPTSX.INDX",    "TSX"),
    ("SPTSX.INDX",     "TSX alt1"),
    ("TSX.INDX",       "TSX alt2"),
    ("GSPTSE.INDX",    "TSX alt3"),
    ("TXCX.INDX",      "TSX alt4"),
]

for lt, name in CANDIDATES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_3D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {name} ({lt}): date={last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {name} ({lt}): vuoto")
