import os, requests, json

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for yticker in ["AAPL", "NVDA", "MSFT"]:
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yticker}"
    r = requests.get(url, params={"modules": "defaultKeyStatistics"}, headers=HEADERS, timeout=15)
    print(f"\n=== {yticker} (status {r.status_code}) ===")
    try:
        d = r.json()
        beta = d.get("quoteSummary",{}).get("result",[{}])[0].get("defaultKeyStatistics",{}).get("beta",{})
        print("Beta raw:", beta)
    except Exception as e:
        print("ERRORE parsing:", e, r.text[:300])
