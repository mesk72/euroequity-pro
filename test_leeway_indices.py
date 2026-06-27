import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_5D      = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

# Leggi i ticker numerici BR con tutti i campi
print("\n=== Ticker numerici BR dal DB ===")
r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "ticker,exchange,company,yahoo_ticker,isin",
            "exchange": "eq.BR", "in_universe": "eq.true",
            "ticker": "like.0*", "limit": "20"})
data = r.json()
if isinstance(data, list):
    for d in data:
        print(f"  ticker={d.get('ticker')} yahoo={d.get('yahoo_ticker')} isin={d.get('isin')} company={d.get('company')}")

# Test US con .NASDAQ e .NYSE
print("\n=== US vuoti — test suffissi ===")
US_VUOTI = ["BW", "KRG", "POST", "FE", "KEY", "UAL", "DOW", "EQR"]
for t in US_VUOTI:
    found = False
    for suffix in [".US", ".NASDAQ", ".NYSE", ".NSDQ"]:
        lt = t + suffix
        r2 = test(lt)
        if r2[1]:
            print(f"  OK {lt}: {r2[1]}")
            found = True
            break
    if not found:
        print(f"  !! {t}: vuoto con tutti i suffissi")

# Test OM spazio vs trattino
print("\n=== OM Stoccolma ===")
for name, dash, space in [
    ("SCA B", "SCA-B.ST", "SCA B.ST"),
    ("VOLV B", "VOLV-B.ST", "VOLV B.ST"),
    ("HEXA B", "HEXA-B.ST", "HEXA B.ST"),
]:
    r1 = test(dash); r2 = test(space)
    if r1[1]: print(f"  OK trattino {dash}: {r1[1]}")
    elif r2[1]: print(f"  OK spazio {space}: {r2[1]}")
    else: print(f"  !! {name}: vuoto")
