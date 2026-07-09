import os, requests
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
url = f"https://api.leeway.tech/api/v1/public/historicalquotes/HSBA.L?apitoken={LEEWAY_KEY}&from=2026-07-01&to=2026-07-09"
r = requests.get(url, timeout=20)
print(f"HTTP {r.status_code}")
data = r.json()
if isinstance(data, list):
    for row in sorted(data, key=lambda x: x.get("date","")):
        print(row)
else:
    print(data)
