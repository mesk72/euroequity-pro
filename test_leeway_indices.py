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
    # OB — Oslo
    ("OB Oslo", ["EQNR.OL", "DNB.OL", "TEL.OL", "MOWI.OL", "YAR.OL"]),

    # SWX — Zurigo (Roche era vuoto)
    ("SWX Zurigo", ["ROG.SW", "RO.SW", "NESN.SW", "ABBN.SW", "NOVN.SW", "ZURN.SW", "LONN.SW"]),

    # NGM — Stoccolma small cap
    ("NGM Stoccolma", ["SOBI.ST", "CINT.ST", "BETS-B.ST", "BETS B.ST", "BETB.ST"]),

    # AIM — Londra small cap
    ("AIM London", ["BOO.AIM", "THRG.AIM", "KAPE.AIM", "GGP.AIM", "ABBY.AIM"]),

    # AT — Vienna (verifica)
    ("AT Vienna", ["OMV.AT", "VIG.AT", "EBS.AT", "ANDR.AT", "POST.AT"]),

    # VI — Vienna (exchange diverso da AT?)
    ("VI Vienna", ["OMV.VI", "VIG.VI", "EBS.VI", "ANDR.VI"]),

    # PA — verifica titoli vuoti del test precedente
    ("PA Parigi vuoti", ["AI.PA", "BN.PA", "ATO.PA", "AKE.PA", "ALFEN.PA"]),

    # BR — verifica regola punto→nulla
    ("BR punto nulla", ["AGFB.BR", "AGF.BR", "AGF-B.BR", "ARGX.BR", "ABI.BR"]),
]

for label, tickers in TESTS:
    print(f"\n=== {label} ===")
    for lt in tickers:
        result = test(lt)
        if result[1]:
            print(f"  OK {lt}: {result[1]} close={result[2]}")
        else:
            print(f"  !! {lt}: vuoto")
