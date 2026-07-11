import os, requests
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
for ticker in ["JPM", "AAPL", "MSFT"]:
    url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{ticker}?apitoken={LEEWAY_KEY}&from=2026-07-01&to=2026-07-11"
    r = requests.get(url, timeout=20)
    print(f"=== {ticker}: HTTP {r.status_code} ===")
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            for row in sorted(data, key=lambda x: x.get("date","")):
                print(f"  {row}")
        else:
            print(f"  {data}")
    else:
        print(f"  {r.text[:300]}")
