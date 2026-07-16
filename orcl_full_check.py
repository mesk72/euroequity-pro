import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
SYM = "ORCL"

def call(endpoint, params=None):
    p = params or {}
    p["symbol"] = SYM
    p["apikey"] = API_KEY
    r = requests.get(f"https://api.twelvedata.com/{endpoint}", params=p)
    print(f"\n=== {endpoint} {params or ''} ===")
    print(json.dumps(r.json(), indent=1)[:2000])

call("earnings")
call("earnings_estimate", {"period":"annual"})
call("revenue_estimate", {"period":"annual"})
call("eps_trend", {"period":"annual"})
call("statistics")
call("time_series", {"interval":"1day","outputsize":"1","adjust":"all"})
