import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

TARGETS = [
    ("VOD", "XLON"),
    ("UCG", "XMIL"),
    ("MSFT", None),
]

def call(endpoint, sym, mic, params=None):
    p = params or {}
    p["symbol"] = sym
    if mic: p["mic_code"] = mic
    p["apikey"] = API_KEY
    r = requests.get(f"https://api.twelvedata.com/{endpoint}", params=p)
    print(f"\n=== {sym} ({mic or 'default'}) / {endpoint} {params or ''} (status {r.status_code}) ===")
    print(json.dumps(r.json(), indent=1)[:2200])

for sym, mic in TARGETS:
    call("earnings", sym, mic)
    call("earnings_estimate", sym, mic, {"period":"annual"})
    call("revenue_estimate", sym, mic, {"period":"annual"})
    call("eps_trend", sym, mic, {"period":"annual"})
    call("statistics", sym, mic)
