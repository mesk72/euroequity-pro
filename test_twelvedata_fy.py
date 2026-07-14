import os, requests, json, time

API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
BASE = "https://api.twelvedata.com"

tickers = ["NVDA", "JPM", "ASML", "BNP"]

def call(endpoint, symbol, extra_params=None):
    params = {"symbol": symbol, "apikey": API_KEY}
    if extra_params:
        params.update(extra_params)
    try:
        r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=20)
        return r.status_code, r.json()
    except Exception as e:
        return None, {"error": str(e)}

for t in tickers:
    print(f"\n{'='*70}")
    print(f"TICKER: {t}")
    print('='*70)

    print("\n--- /earnings (period=latest) — LAST REPORTING DATE ---")
    status, data = call("earnings", t, {"period": "latest"})
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:1800])
    time.sleep(1)

    print("\n--- /statistics — most_recent_quarter, fiscal_year_ends ---")
    status, data = call("statistics", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:3000])
    time.sleep(1)

    print("\n--- /earnings_estimate — EPS FY1/FY2 ---")
    status, data = call("earnings_estimate", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:3000])
    time.sleep(1)

    print("\n--- /eps_trend — storico EPS, verifica se distingue normalized/GAAP ---")
    status, data = call("eps_trend", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])
    time.sleep(1)

    print("\n--- /revenue_estimate (tentativo, nome endpoint da verificare) ---")
    status, data = call("revenue_estimate", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])
    time.sleep(1)

    print("\n--- /growth_estimates ---")
    status, data = call("growth_estimates", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])
    time.sleep(2)
