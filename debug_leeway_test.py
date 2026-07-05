import os, requests

LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE = "https://api.leeway.tech/api/v1/public"

test_tickers = ["7203.TSE", "0700.HK", "BHP.AU", "005930.KO", "D05.SG"]

for t in test_tickers:
    url = f"{LEEWAY_BASE}/historicalquotes/{t}?apitoken={LEEWAY_KEY}&from=2026-06-01&to=2026-07-05"
    try:
        r = requests.get(url, timeout=15)
        print(f"{t}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  righe: {len(data) if isinstance(data, list) else 'non-lista'}")
            if isinstance(data, list) and data:
                print(f"  ultima riga: {data[-1]}")
        else:
            print(f"  risposta: {r.text[:200]}")
    except Exception as e:
        print(f"{t}: ERRORE {e}")
    print()
