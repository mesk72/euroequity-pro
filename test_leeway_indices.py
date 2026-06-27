import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_5D      = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

def test(lt):
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=8)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return (lt, last.get("date"), last.get("close"))
    except: pass
    return (lt, None, None)

print("TODAY:", TODAY)

TESTS = [
    # Vienna — AT vs VI suffisso
    ("AT/VI Vienna", [
        "OMV.AT", "OMV.VI", "VIG.AT", "VIG.VI",
        "EBS.AT", "EBS.VI", "ANDR.AT", "ANDR.VI",
        "POST.AT", "POST.VI", "RBI.AT", "RBI.VI",
    ]),

    # Zurigo SWX — Roche e altri
    ("SWX Zurigo", [
        "ROG.SW", "RO.SW", "ROG.SWX",
        "NESN.SW", "ABBN.SW", "NOVN.SW",
        "ZURN.SW", "LONN.SW", "GIVN.SW",
        "SGSN.SW", "CFR.SW", "SLHN.SW",
    ]),

    # Oslo OB
    ("OB Oslo", [
        "EQNR.OL", "DNB.OL", "TEL.OL",
        "MOWI.OL", "YAR.OL", "ORK.OL",
        "NHY.OL", "SALM.OL", "SUBC.OL",
    ]),
]

for label, tickers in TESTS:
    print(f"\n=== {label} ===")
    for lt in tickers:
        result = test(lt)
        if result[1]:
            print(f"  OK {lt}: {result[1]} close={result[2]}")
        else:
            print(f"  !! {lt}: vuoto")
