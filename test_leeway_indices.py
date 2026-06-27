import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_10D    = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

def test(lt):
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        last = sorted(data, key=lambda x: x["date"])[-1]
        print(f"  OK {lt}: {last.get('date')} close={last.get('close')}")
    else:
        print(f"  !! {lt}: vuoto")

print("TODAY:", TODAY)
print("FROM:", FROM_10D)
print()

# XETRA — STO3 col punto rimosso
test("STO3.XETRA")

# LSE — punto finale rimosso
test("UU.LSE")   # era UU..LSE
test("QQ.LSE")   # era QQ..LSE  
test("AO.LSE")   # era AO..LSE
