import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print()

# 2 titoli per ogni borsa EU (esclusa Grecia)
TICKERS = [
    # Italia MIL
    ("ENI.MI",     "ENI",          "MIL"),
    ("ENEL.MI",    "ENEL",         "MIL"),
    # Germania XETRA
    ("SAP.XETRA",  "SAP",          "XETRA"),
    ("SIE.XETRA",  "Siemens",      "XETRA"),
    # Francia PA
    ("MC.PA",      "LVMH",         "PA"),
    ("TTE.PA",     "TotalEnergies","PA"),
    # Spagna MC
    ("SAN.MC",     "Santander",    "MC"),
    ("IBE.MC",     "Iberdrola",    "MC"),
    # Olanda AS
    ("ASML.AS",    "ASML",         "AS"),
    ("HEIA.AS",    "Heineken",     "AS"),
    # Belgio BR
    ("UCB.BR",     "UCB",          "BR"),
    ("ABI.BR",     "AB InBev",     "BR"),
    # Portogallo LS
    ("EDP.LS",     "EDP",          "LS"),
    ("GALP.LS",    "Galp",         "LS"),
    # Austria VI
    ("OMV.VI",     "OMV",          "VI"),
    ("VIG.VI",     "VIG",          "VI"),
    # Irlanda IR
    ("CRH.IR",     "CRH",          "IR"),
    ("AIB.IR",     "AIB",          "IR"),
    # Svizzera SWX
    ("NESN.SW",    "Nestle",       "SWX"),
    ("ROG.SW",     "Roche",        "SWX"),
    # Svezia OM
    ("VOLV-B.ST",  "Volvo",        "OM"),
    ("ERIC-B.ST",  "Ericsson",     "OM"),
    # Norvegia OB
    ("EQNR.OL",    "Equinor",      "OB"),
    ("DNB.OL",     "DNB",          "OB"),
    # Danimarca CPSE
    ("NOVO-B.CO",  "Novo Nordisk", "CPSE"),
    ("MAERSK-B.CO","Maersk",       "CPSE"),
    # Finlandia HE
    ("NOKIA.HE",   "Nokia",        "HE"),
    ("FORTUM.HE",  "Fortum",       "HE"),
    # UK LSE
    ("HSBA.LSE",   "HSBC",         "LSE"),
    ("BP.LSE",     "BP",           "LSE"),
]

for lt, name, exchange in TICKERS:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {exchange} {name} ({lt}): {last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {exchange} {name} ({lt}): vuoto HTTP {r.status_code}")
