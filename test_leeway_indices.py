import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_3D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

ALL_INDICES = [
    # EU
    ("GDAXI.INDX",    "DAX"),
    ("FCHI.INDX",     "CAC 40"),
    ("FTSEMIB.MI",    "FTSE MIB (attuale)"),
    ("FTMIB.INDX",    "FTSE MIB (alt1)"),
    ("FTSEMIB.INDX",  "FTSE MIB (alt2)"),
    ("FTSE.INDX",     "FTSE 100 (attuale)"),
    ("UKX.INDX",      "FTSE 100 (alt1)"),
    ("FTSE100.INDX",  "FTSE 100 (alt2)"),
    ("SSMI.INDX",     "SMI"),
    ("ATX.INDX",      "ATX"),
    ("AEX.INDX",      "AEX"),
    ("IBEX.INDX",     "IBEX 35"),
    ("BFX.INDX",      "BEL 20"),
    ("OMXS30.INDX",   "OMX Stockholm"),
    ("OMXC25.INDX",   "OMX Copenhagen"),
    ("OMXHPI.INDX",   "OMX Helsinki"),
    ("ISEQ.INDX",     "ISEQ"),
    ("STOXX50E.INDX", "Euro Stoxx 50"),
    ("SXXP.INDX",     "STOXX 600"),
    ("PSI20.INDX",    "PSI 20"),
    # NA
    ("GSPC.INDX",     "S&P 500"),
    ("IXIC.INDX",     "Nasdaq"),
    ("DJI.INDX",      "Dow Jones"),
    ("OSPTSX.INDX",   "TSX"),
]

for lt, name in ALL_INDICES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_3D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {name} ({lt}): date={last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {name} ({lt}): vuoto")
