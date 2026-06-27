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

# Test US — i vuoti erano BW, KRG, POST, FE ecc.
# Proviamo con .NYSE, .NASDAQ, senza suffisso
print("\n=== US ticker vuoti — formati alternativi ===")
US_VUOTI = ["BW", "KRG", "POST", "FE", "KEY", "UAL", "DOW", "EQR", "TEVA", "CINF", "NVT", "OTIS"]
for t in US_VUOTI:
    results = []
    for suffix in [".US", ".NYSE", ".NASDAQ", ".NSDQ"]:
        lt = t + suffix
        r = test(lt)
        if r[1]:
            results.append(f"OK {lt}: {r[1]} close={r[2]}")
            break
    if results:
        print(f"  {results[0]}")
    else:
        print(f"  !! {t}: vuoto con tutti i suffissi")

# Test OM — spazio vs trattino
print("\n=== OM Stoccolma — spazio vs trattino ===")
OM_TESTS = [
    ("SCA B", "SCA-B.ST", "SCA B.ST"),
    ("SKA B", "SKA-B.ST", "SKA B.ST"),
    ("VOLV B", "VOLV-B.ST", "VOLV B.ST"),
    ("HEXA B", "HEXA-B.ST", "HEXA B.ST"),
]
for name, with_dash, with_space in OM_TESTS:
    r1 = test(with_dash)
    r2 = test(with_space)
    if r1[1]:
        print(f"  OK trattino: {with_dash}: {r1[1]}")
    elif r2[1]:
        print(f"  OK spazio:   {with_space}: {r2[1]}")
    else:
        print(f"  !! {name}: vuoto con entrambi")

# Test TSE alfanumerici
print("\n=== TSE alfanumerici ===")
for lt in ["141A.TSE", "417A.TSE", "285A.TSE"]:
    r = test(lt)
    if r[1]: print(f"  OK {lt}: {r[1]} close={r[2]}")
    else: print(f"  !! {lt}: vuoto")

# Test AS vuoti specifici
print("\n=== AS Amsterdam vuoti ===")
for t in ["HOLCO", "ECT", "AD", "RAND", "AGN", "SBMO", "OCI", "INGA", "VPK"]:
    lt = t + ".AS"
    r = test(lt)
    if r[1]: print(f"  OK {lt}: {r[1]}")
    else: print(f"  !! {lt}: vuoto")
