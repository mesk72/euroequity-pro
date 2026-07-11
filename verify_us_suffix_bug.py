import os, requests
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
for ticker in ["JPM.US", "JPM", "AAPL.US", "AAPL"]:
    url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{ticker}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
    r = requests.get(url, timeout=20)
    print(f"{ticker}: HTTP {r.status_code}", r.json() if r.status_code==200 else r.text[:150])
