import os, requests, time
from datetime import datetime, timezone
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance")

def yahoo_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "SGX": return ticker + ".SI"
    return ticker

results = {"SEHK": [], "SGX": []}
fail = 0
for exch in ["SEHK","SGX"]:
    tickers = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{exch}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        tickers.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"{exch}: {len(tickers)} titoli da processare")

    for i, s in enumerate(tickers):
        ticker = s["ticker"]
        yt = yahoo_ticker(ticker, exch)
        try:
            info = yf.Ticker(yt).info
            ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
            if ts:
                month = datetime.fromtimestamp(ts, tz=timezone.utc).month
                results[exch].append({"ticker": ticker, "exchange": exch, "fiscal_month": str(month)})
            else:
                fail += 1
        except Exception:
            fail += 1
        if (i+1) % 100 == 0:
            print(f"  ...{i+1}/{len(tickers)} — trovati finora {len(results[exch])}")
        time.sleep(0.2)

print(f"\nSEHK trovati: {len(results['SEHK'])}")
print(f"SGX trovati: {len(results['SGX'])}")
print(f"Falliti: {fail}")

import csv
with open("fiscal_month_hk_sgx.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","fiscal_month"])
    w.writeheader()
    for exch in results:
        for row in results[exch]:
            w.writerow(row)
print("Scritto fiscal_month_hk_sgx.csv")
