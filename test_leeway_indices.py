import os, requests
from datetime import datetime, timedelta

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = datetime.now().strftime("%Y-%m-%d")
FROM_5D     = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

print("=" * 60)
print("TEST 1: INDICI — tutti i campi")
print("=" * 60)
for lt, name in [
    ("FTSEMIB.MI", "FTSE MIB"),
    ("SSMI.INDX",  "SMI"),
    ("ATX.INDX",   "ATX"),
    ("GDAXI.INDX", "DAX"),
]:
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5D}&to={TODAY}"
    r = requests.get(url, timeout=10)
    print(f"\n{name} ({lt}) — HTTP {r.status_code}")
    if r.status_code == 200:
        data = sorted(r.json() or [], key=lambda x: x.get("date",""))
        for row in data[-3:]:  # ultimi 3 giorni
            print(f"  date={row.get('date')} open={row.get('open')} high={row.get('high')} low={row.get('low')} close={row.get('close')} adj={row.get('adjusted_close')}")

print()
print("=" * 60)
print("TEST 2: TICKER APAC — formato ticker")
print("=" * 60)
# Toyota: ticker TSE = 7203 → proviamo 7203.T
# Tencent: ticker SEHK = 700 → proviamo 0700.HK e 700.HK
# BHP: ticker ASX = BHP → proviamo BHP.AX
for lt, name in [
    ("7203.T",   "Toyota (TSE)"),
    ("0700.HK",  "Tencent 0700.HK"),
    ("700.HK",   "Tencent 700.HK"),
    ("BHP.AX",   "BHP (ASX)"),
    ("CBA.AX",   "Commonwealth Bank (ASX)"),
]:
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5D}&to={TODAY}"
    r = requests.get(url, timeout=10)
    data = r.json() if r.status_code == 200 else []
    last = sorted(data, key=lambda x: x.get("date",""))[-1] if isinstance(data, list) and data else None
    if last:
        print(f"  ✅ {name}: close={last.get('close')} date={last.get('date')}")
    else:
        print(f"  ❌ {name}: HTTP {r.status_code} — {str(r.text)[:50]}")
