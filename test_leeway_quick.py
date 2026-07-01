import os, requests, time

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"
TODAY       = "2026-06-27"
FROM_5D     = "2026-06-20"

# Un titolo noto per ogni mercato
TEST_TICKERS = [
    ("ENI.MI",    "MIL",  "ENI"),
    ("SAP.XETRA", "XETRA","SAP"),
    ("MC.PA",     "PA",   "LVMH"),
    ("AZN.LSE",   "LSE",  "AstraZeneca"),
    ("VOLV-B.ST", "OM",   "Volvo"),
    ("NESN.SW",   "SWX",  "Nestle"),
    ("NOVO-B.CO", "CPSE", "Novo Nordisk"),
    ("DNB.OL",    "OB",   "DNB"),
    ("ASML.AS",   "AS",   "ASML"),
    ("IBE.MC",    "MC",   "Iberdrola"),
    ("ABI.BR",    "BR",   "AB InBev"),
    ("SAMPO.HE",  "HE",   "Sampo"),
    ("AAPL.US",   "US",   "Apple"),
    ("RY.TO",     "TSX",  "Royal Bank"),
    ("7203.TSE",  "TSE",  "Toyota"),
    ("0700.HK",   "SEHK", "Tencent"),
    ("BHP.AU",    "ASX",  "BHP"),
]

print(f"LEEWAY_KEY: {LEEWAY_KEY[:8]}...")
print(f"Test {len(TEST_TICKERS)} mercati — FROM={FROM_5D} TO={TODAY}")
print()

ok = fail = 0
for yt, exchange, name in TEST_TICKERS:
    url = f"{LEEWAY_BASE}/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from={FROM_5D}&to={TODAY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            last = sorted(r.json(), key=lambda x: x["date"])[-1]
            print(f"  OK {exchange:<6} {yt:<15} {name:<20} close={last.get('close')} date={last.get('date')}")
            ok += 1
        else:
            print(f"  !! {exchange:<6} {yt:<15} {name:<20} HTTP={r.status_code} empty={not r.json()}")
            fail += 1
    except Exception as e:
        print(f"  !! {exchange:<6} {yt:<15} {name:<20} ERROR={e}")
        fail += 1
    time.sleep(0.5)

print(f"\nRisultato: OK={ok} FAIL={fail}")
print("Leeway FUNZIONA" if fail == 0 else f"ATTENZIONE: {fail} mercati con problemi")
