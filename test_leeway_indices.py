import os, requests
from datetime import datetime, timedelta
from collections import Counter

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
            return last.get("date"), last.get("close")
    except: pass
    return None, None

print("TODAY:", TODAY)

# Leggi tutti gli exchange distinti per titoli US in universe
print("\n=== Exchange distinti nel DB per titoli in universe ===")
r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "exchange", "in_universe": "eq.true", "limit": "5000"})
data = r.json()
if isinstance(data, list):
    counts = Counter(d["exchange"] for d in data)
    for ex, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {ex}: {cnt}")

# Test OM spazio nel loop — come viene costruito il ticker
print("\n=== OM: verifica ticker nel DB con spazio ===")
r2 = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "ticker,exchange", "exchange": "eq.OM",
            "in_universe": "eq.true", "ticker": "like.% %", "limit": "10"})
data2 = r2.json()
if isinstance(data2, list):
    for d in data2:
        ticker = d["ticker"]
        lt_space = ticker + ".ST"
        lt_dash  = ticker.replace(" ", "-") + ".ST"
        d1, c1 = test(lt_space)
        d2, c2 = test(lt_dash)
        print(f"  DB ticker='{ticker}'")
        print(f"    spazio  {lt_space}: {'OK '+str(d1) if d1 else 'vuoto'}")
        print(f"    trattino {lt_dash}: {'OK '+str(d2) if d2 else 'vuoto'}")
