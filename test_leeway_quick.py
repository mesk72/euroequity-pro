import os, requests, time

LEEWAY_KEY  = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"

TEST_TICKERS = [
    # EU — ultima chiusura 30 giugno
    ("ENI.MI",    "MIL",  "ENI",          "2026-07-01", "2026-06-25"),
    ("SAP.XETRA", "XETRA","SAP",          "2026-07-01", "2026-06-25"),
    ("MC.PA",     "PA",   "LVMH",         "2026-07-01", "2026-06-25"),
    ("AZN.LSE",   "LSE",  "AstraZeneca",  "2026-07-01", "2026-06-25"),
    ("VOLV-B.ST", "OM",   "Volvo",        "2026-07-01", "2026-06-25"),
    ("NESN.SW",   "SWX",  "Nestle",       "2026-07-01", "2026-06-25"),
    ("NOVO-B.CO", "CPSE", "Novo Nordisk", "2026-07-01", "2026-06-25"),
    ("DNB.OL",    "OB",   "DNB",          "2026-07-01", "2026-06-25"),
    ("ASML.AS",   "AS",   "ASML",         "2026-07-01", "2026-06-25"),
    ("ABI.BR",    "BR",   "AB InBev",     "2026-07-01", "2026-06-25"),
    # US — ultima chiusura 30 giugno
    ("AAPL.US",   "US",   "Apple",        "2026-07-01", "2026-06-25"),
    ("RY.TO",     "TSX",  "Royal Bank",   "2026-07-01", "2026-06-25"),
    # APAC — chiusi stamattina 1 luglio
    ("7203.TSE",  "TSE",  "Toyota",       "2026-07-01", "2026-06-25"),
    ("0700.HK",   "SEHK", "Tencent",      "2026-07-01", "2026-06-25"),
    ("BHP.AU",    "ASX",  "BHP",          "2026-07-01", "2026-06-25"),
]

print(f"LEEWAY_KEY: {LEEWAY_KEY[:8]}...")
print(f"Oggi: 1 luglio 2026 ore 13:36 CET")
print()
print(f"{'Exchange':<8} {'Ticker':<15} {'Nome':<20} {'Ultima data':<14} {'Close'}")
print("-" * 68)

ok = fail = 0
for yt, exchange, name, to_date, from_date in TEST_TICKERS:
    url = f"{LEEWAY_BASE}/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from={from_date}&to={to_date}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            last = sorted(r.json(), key=lambda x: x["date"])[-1]
            date = last.get("date")
            close = last.get("close") or last.get("adjusted_close")
            if date == "2026-07-01":
                status = "✅ OGGI"
            elif date == "2026-06-30":
                status = "✅ 30/06"
            else:
                status = f"⚠️ {date}"
            print(f"  {exchange:<8} {yt:<15} {name:<20} {date:<14} {close} {status}")
            ok += 1
        else:
            print(f"  {exchange:<8} {yt:<15} {name:<20} {'VUOTO':<14} HTTP={r.status_code} ❌")
            fail += 1
    except Exception as e:
        print(f"  {exchange:<8} {yt:<15} {name:<20} {'ERROR':<14} {e} ❌")
        fail += 1
    time.sleep(0.5)

print(f"\nOK={ok} FAIL={fail}")
