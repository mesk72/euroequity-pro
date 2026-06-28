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
        print(f"  !! {lt}: vuoto HTTP {r.status_code}")

print("TODAY:", TODAY)
print()

# Titoli greci noti — OPAP (lotterie), Eurobank, Alpha Bank, Mytilineos
print("=== GRECIA — formati alternativi ===")
for lt in [
    "OPAP.AT", "OPAP.GR", "OPAP.XATH", "OPAP.ATH",
    "EUROB.AT", "EUROB.GR", "EUROB.ATH",
    "ALPHA.AT", "ALPHA.GR",
    "MYTIL.AT", "MYTIL.GR",
    "ETE.AT", "ETE.GR",
]:
    test(lt)
