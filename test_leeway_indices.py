import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

# 5 ticker vuoti per borsa dal test precedente
# Da verificare se sono problema di formato o copertura
SAMPLES = [
    # MIL
    ("MONC.MI",    "MIL", "Moncler"),
    ("RACE.MI",    "MIL", "Ferrari"),
    # XETRA
    ("MBG.XETRA",  "XETRA", "Mercedes"),
    ("VOW3.XETRA", "XETRA", "VW"),
    # PA
    ("AI.PA",      "PA", "Air Liquide"),
    ("BN.PA",      "PA", "Danone"),
    # LSE
    ("SHEL.LSE",   "LSE", "Shell"),
    ("AZN.LSE",    "LSE", "AstraZeneca"),
    # OM
    ("ASSA-B.ST",  "OM", "Assa Abloy"),
    ("ATCO-A.ST",  "OM", "Atlas Copco"),
    # SWX
    ("ABBN.SW",    "SWX", "ABB"),
    ("NOVN.SW",    "SWX", "Novartis"),
    # TSE
    ("6758.TSE",   "TSE", "Sony"),
    ("9432.TSE",   "TSE", "NTT"),
    # ASX
    ("ANZ.AU",     "ASX", "ANZ Bank"),
    ("WBC.AU",     "ASX", "Westpac"),
    # TSX
    ("RY.TO",      "TSX", "Royal Bank"),
    ("TD.TO",      "TSX", "TD Bank"),
    # US
    ("AAPL.US",    "US", "Apple"),
    ("MSFT.US",    "US", "Microsoft"),
    ("NVDA.US",    "US", "Nvidia"),
]

for lt, exchange, name in SAMPLES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=8)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {exchange} {name} ({lt}): {last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {exchange} {name} ({lt}): vuoto")
