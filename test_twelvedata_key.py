import os, requests

API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

print("=== Test 1: api_usage (verifica piano attuale) ===")
r = requests.get(f"https://api.twelvedata.com/api_usage?apikey={API_KEY}")
print("Status:", r.status_code)
print(r.text[:500])

print("\n=== Test 2: statistics NVDA (endpoint fondamentali) ===")
r2 = requests.get(f"https://api.twelvedata.com/statistics?symbol=NVDA&apikey={API_KEY}")
print("Status:", r2.status_code)
print(r2.text[:500])

print("\n=== Test 3: earnings_estimate NVDA ===")
r3 = requests.get(f"https://api.twelvedata.com/earnings_estimate?symbol=NVDA&apikey={API_KEY}")
print("Status:", r3.status_code)
print(r3.text[:500])

print("\n=== Test 4: eps_trend NVDA ===")
r4 = requests.get(f"https://api.twelvedata.com/eps_trend?symbol=NVDA&apikey={API_KEY}")
print("Status:", r4.status_code)
print(r4.text[:500])

print("\n=== Test 5: revenue_estimate NVDA ===")
r5 = requests.get(f"https://api.twelvedata.com/revenue_estimate?symbol=NVDA&apikey={API_KEY}")
print("Status:", r5.status_code)
print(r5.text[:500])
