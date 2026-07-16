import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
SYM = "HRB"

r0 = requests.get("https://api.twelvedata.com/statistics", params={"symbol":SYM,"apikey":API_KEY})
print("fiscal_year_ends:", r0.json().get("statistics",{}).get("financials",{}).get("fiscal_year_ends"))

r1 = requests.get("https://api.twelvedata.com/earnings_estimate", params={"symbol":SYM,"period":"annual","apikey":API_KEY})
print("\n=== earnings_estimate annual ===")
print(json.dumps(r1.json(), indent=1))

r2 = requests.get("https://api.twelvedata.com/eps_trend", params={"symbol":SYM,"period":"annual","apikey":API_KEY})
print("\n=== eps_trend annual ===")
print(json.dumps(r2.json(), indent=1))

r3 = requests.get("https://api.twelvedata.com/earnings", params={"symbol":SYM,"apikey":API_KEY})
print("\n=== earnings (storico reale) ===")
print(json.dumps(r3.json(), indent=1)[:1200])
