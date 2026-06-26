import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_3D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

CANDIDATES = [
    # FTSE MIB — tutti i formati possibili
    ("I945.INDX",      "FTSE MIB I945"),
    ("FMIB.INDX",      "FTSE MIB FMIB"),
    ("FTSEMIB",        "FTSE MIB no suffix"),
    ("MIB30.INDX",     "MIB30"),
    ("FTSEMIB.BIT",    "FTSE MIB .BIT"),
    ("FTSEMIB.MI",     "FTSE MIB .MI"),
    ("IT40.INDX",      "IT40"),
    ("FTMIB.MI",       "FTMIB.MI"),
    # FTSE 100 — tutti i formati possibili
    ("FTSE100",        "FTSE 100 no suffix"),
    ("FTSE.UK",        "FTSE.UK"),
    ("UKX.LSE",        "UKX.LSE"),
    ("FTSE.GB",        "FTSE.GB"),
    ("TASI.INDX",      "FTSE alt TASI"),
    ("FTSEUK.INDX",    "FTSEUK.INDX"),
    ("FTSEGB.INDX",    "FTSEGB.INDX"),
    ("I010.INDX",      "FTSE I010"),
    # ISEQ
    ("ISEQX.INDX",     "ISEQ alt"),
    ("ISE.INDX",       "ISE.INDX"),
    ("ISEQ.IR",        "ISEQ.IR"),
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
