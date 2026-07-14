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

    print("\n--- /statistics ---")
    status, data = call("statistics", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2500])

    time.sleep(1)
    print("\n--- /earnings (period=latest) — LAST REPORTING DATE ---")
    status, data = call("earnings", t, {"period": "latest"})
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])

    time.sleep(1)
    print("\n--- /earnings_estimate ---")
    status, data = call("earnings_estimate", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2500])

    time.sleep(1)
    print("\n--- /eps_trend ---")
    status, data = call("eps_trend", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])

    time.sleep(1)
    print("\n--- /eps_revisions ---")
    status, data = call("eps_revisions", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:2000])

    time.sleep(1)
    print("\n--- /profile ---")
    status, data = call("profile", t)
    print(f"HTTP {status}")
    print(json.dumps(data, indent=2)[:1500])

    time.sleep(2)
