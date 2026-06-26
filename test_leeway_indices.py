import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

print("TODAY:", TODAY)
print("FROM:", FROM_5D)
print()

# Test Australia — BHP, CBA, CSL
print("=== AUSTRALIA (ASX) ===")
for ticker, lt in [("BHP", "BHP.AX"), ("CBA", "CBA.AX"), ("CSL", "CSL.AX")]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        data = sorted(data, key=lambda x: x["date"])
        last = data[-1]
        print(f"  {lt}: ultima data={last['date']} close={last.get('close')} adj={last.get('adjusted_close')}")
    else:
        print(f"  {lt}: HTTP {r.status_code} — {str(r.text)[:100]}")

print()
print("=== GIAPPONE (TSE) ===")
for ticker, lt in [("7203", "7203.TSE"), ("9984", "9984.TSE"), ("8306", "8306.TSE")]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        data = sorted(data, key=lambda x: x["date"])
        last = data[-1]
        print(f"  {lt}: ultima data={last['date']} close={last.get('close')} adj={last.get('adjusted_close')}")
    else:
        print(f"  {lt}: HTTP {r.status_code} — {str(r.text)[:100]}")

print()
print("=== HONG KONG (SEHK) ===")
for ticker, lt in [("700", "0700.HK"), ("941", "0941.HK"), ("5", "0005.HK")]:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if data:
        data = sorted(data, key=lambda x: x["date"])
        last = data[-1]
        print(f"  {lt}: ultima data={last['date']} close={last.get('close')} adj={last.get('adjusted_close')}")
    else:
        print(f"  {lt}: HTTP {r.status_code} — {str(r.text)[:100]}")
