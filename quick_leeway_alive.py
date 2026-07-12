import os, requests
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
print(f"LEEWAY_KEY presente: {bool(LEEWAY_KEY)}, lunghezza: {len(LEEWAY_KEY)}")
url = f"https://api.leeway.tech/api/v1/public/historicalquotes/JPM.US?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
r = requests.get(url, timeout=15)
print(f"HTTP {r.status_code}")
print(r.text[:300])
