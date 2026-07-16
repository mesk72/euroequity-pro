import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
r = requests.get("https://api.twelvedata.com/eps_trend", params={"symbol":"NVDA","period":"annual","apikey":API_KEY})
print("Status:", r.status_code)
print(json.dumps(r.json(), indent=1)[:2000])
