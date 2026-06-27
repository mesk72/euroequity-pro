import os, requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
print()

# Test formati alternativi per ogni problema identificato
TESTS = [
    # CPSE — spazi nel ticker
    ("CPSE spazio→trattino", ["AMBU-B.CO", "AMBU B.CO", "AMBUB.CO", "CARL-B.CO", "COLO-B.CO", "AGF-B.CO", "ALK-B.CO"]),
    
    # TSX — doppio punto
    ("TSX doppio punto", ["AD-UN.TO", "AD.UN.TO", "ADUN.TO", "ACO-X.TO", "ACO.X.TO", "AGF-B.TO", "AGF.B.TO"]),
    
    # LSE — punto finale
    ("LSE punto finale", ["AO.LSE", "AO.L", "AOLTD.LSE", "AML.LSE", "AML.L", "ABF.LSE", "ABF.L"]),
    
    # AS — blue chip vuoti
    ("AS blue chip", ["ASML.AS", "ADYEN.AS", "AKZA.AS", "ARCAD.AS", "APAM.AS", "ASM.AS"]),
    
    # MC — blue chip vuoti  
    ("MC blue chip", ["BBVA.MC", "CABK.MC", "AENA.MC", "ANA.MC", "AMS.MC", "BKT.MC"]),
    
    # LS — blue chip vuoti
    ("LS blue chip", ["EDP.LS", "BCP.LS", "CTT.LS", "NOS.LS", "SON.LS"]),
    
    # MIL — blue chip vuoti
    ("MIL blue chip", ["A2A.MI", "BMPS.MI", "BPE.MI", "AMP.MI", "ARIS.MI"]),
    
    # IR — blue chip vuoti
    ("IR blue chip", ["RYA.IR", "RYAIR.IR", "RY4C.IR", "GL9.IR", "KRZ.IR"]),
    
    # SEHK — zero padding varianti
    ("SEHK padding", ["10.HK", "0010.HK", "100.HK", "0100.HK", "1088.HK", "01088.HK"]),
    
    # US — AAPL vuoto anomalo
    ("US anomalia", ["AAPL.US", "AAPL.NASDAQ", "ABT.US", "ABM.US"]),
    
    # TSE — ticker 4 cifre vuoti
    ("TSE 4 cifre", ["1414.TSE", "1605.TSE", "1801.TSE", "1332.TSE", "1662.TSE"]),
    
    # HE — blue chip vuoti
    ("HE blue chip", ["ELISA.HE", "CTY1S.HE", "CAPMAN.HE", "ENENTO.HE"]),
    
    # BR — ticker normali vuoti
    ("BR blue chip", ["ARGX.BR", "AGFB.BR", "AGF-B.BR", "ACKB.BR", "ABO.BR"]),
    
    # ASX — ticker alfanumerici
    ("ASX special", ["AGL.AU", "ALD.AU", "ALQ.AU", "AFG.AU", "29M.AU", "A1M.AU"]),
]

for label, tickers in TESTS:
    print(f"\n=== {label} ===")
    for lt in tickers:
        result = test(lt)
        if result[1]:
            print(f"  OK {lt}: {result[1]} close={result[2]}")
        else:
            print(f"  !! {lt}: vuoto")
