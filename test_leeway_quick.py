import os, requests, time

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"

# Date corrette per ogni mercato
# APAC: ultima chiusura venerdì 27 giugno
# EU e US: ultima chiusura lunedì 30 giugno

TEST_TICKERS = [
    ("ENI.MI",    "MIL",  "ENI",          "2026-06-30", "2026-06-24"),
    ("SAP.XETRA", "XETRA","SAP",          "2026-06-30", "2026-06-24"),
    ("MC.PA",     "PA",   "LVMH",         "2026-06-30", "2026-06-24"),
    ("AZN.LSE",   "LSE",  "AstraZeneca",  "2026-06-30", "2026-06-24"),
    ("VOLV-B.ST", "OM",   "Volvo",        "2026-06-30", "2026-06-24"),
    ("NESN.SW",   "SWX",  "Nestle",       "2026-06-30", "2026-06-24"),
    ("NOVO-B.CO", "CPSE", "Novo Nordisk", "2026-06-30", "2026-06-24"),
    ("DNB.OL",    "OB",   "DNB",          "2026-06-30", "2026-06-24"),
    ("ASML.AS",   "AS",   "ASML",         "2026-06-30", "2026-06-24"),
    ("IBE.MC",    "MC",   "Iberdrola",    "2026-06-30", "2026-06-24"),
    ("ABI.BR",    "BR",   "AB InBev",     "2026-06-30", "2026-06-24"),
    ("SAMPO.HE",  "HE",   "Sampo",        "2026-06-30", "2026-06-24"),
    ("AAPL.US",   "US",   "Apple",        "2026-06-30", "2026-06-24"),
    ("RY.TO",     "TSX",  "Royal Bank",   "2026-06-30", "2026-06-24"),
    ("7203.TSE",  "TSE",  "Toyota",       "2026-06-27", "2026-06-23"),
    ("0700.HK",   "SEHK", "Tencent",      "2026-06-27", "2026-06-23"),
    ("BHP.AU",    "ASX",  "BHP",          "2026-06-27", "2026-06-23"),
]

print(f"LEEWAY_KEY: {LEEWAY_KEY[:8]}...")
print()
print(f"{'Exchange':<8} {'Ticker':<15} {'Nome':<20} {'Ultima data':<12} {'Close'}")
print("-" * 65)

ok = fail = 0
for yt, exchange, name, to_date, from_date in TEST_TICKERS:
    url = f"{LEEWAY_BASE}/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from={from_date}&to={to_date}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            last = sorted(r.json(), key=lambda x: x["date"])[-1]
            date = last.get("date")
            close = last.get("close") or last.get("adjusted_close")
            status = "✅" if date >= from_date else "⚠️ VECCHIO"
            print(f"  {exchange:<8} {yt:<15} {name:<20} {date:<12} {close} {status}")
            ok += 1
        else:
            print(f"  {exchange:<8} {yt:<15} {name:<20} VUOTO HTTP={r.status_code} ❌")
            fail += 1
    except Exception as e:
        print(f"  {exchange:<8} {yt:<15} {name:<20} ERROR={e} ❌")
        fail += 1
    time.sleep(0.5)

print(f"\nOK={ok} FAIL={fail}")
