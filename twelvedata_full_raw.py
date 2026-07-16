import os, requests, json

API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
SYM = "NVDA"

def call(endpoint, params=None):
    p = params or {}
    p["symbol"] = SYM
    p["apikey"] = API_KEY
    r = requests.get(f"https://api.twelvedata.com/{endpoint}", params=p)
    print(f"\n=== {endpoint} {params or ''} (status {r.status_code}) ===")
    try:
        print(json.dumps(r.json(), indent=1)[:2500])
    except:
        print(r.text[:1000])

# Last reporting date + storico utili reali
call("earnings")

# Stime EPS - proviamo period annuale, non solo trimestrale
call("earnings_estimate", {"period": "annual"})
call("earnings_estimate", {"period": "current_year"})

# Stime ricavi - stesso tentativo annuale
call("revenue_estimate", {"period": "annual"})
call("revenue_estimate", {"period": "current_year"})

# Growth estimates (potrebbe avere FY1/FY2 diretti)
call("growth_estimates")

# Statistics per PB e fiscal year end
call("statistics")

# Prezzi aggiustati per split/dividendi
call("time_series", {"interval":"1day","outputsize":"10","adjust":"all"})
