import os, requests, time
from datetime import datetime, timedelta

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_5D      = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}

LEEWAY_SUFFIX = {
    "MIL": ".MI", "XETRA": ".XETRA", "PA": ".PA",
    "LSE": ".LSE", "US": ".US",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    return ticker + LEEWAY_SUFFIX.get(exchange, "")

def test_ticker(ticker, exchange):
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return lt, True, last.get("date")
        return lt, False, None
    except:
        return lt, False, None

print("TODAY:", TODAY)

EXCHANGES = ["US", "MIL", "XETRA", "PA", "LSE"]

for exchange in EXCHANGES:
    stocks = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker", "in_universe": "eq.true",
                    "exchange": f"eq.{exchange}",
                    "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    ok = []; empty = []
    print(f"\n{exchange}: {len(stocks)} titoli in test...")
    for i, s in enumerate(stocks):
        lt, has_data, date = test_ticker(s["ticker"], exchange)
        if has_data: ok.append((s["ticker"], lt, date))
        else: empty.append((s["ticker"], lt))
        time.sleep(0.5)
        if (i+1) % 100 == 0:
            print(f"  {i+1}/{len(stocks)} ok={len(ok)} vuoti={len(empty)}")

    print(f"{exchange} FINALE: OK={len(ok)} VUOTI={len(empty)}")
    for tk, lt in empty:
        print(f"  {tk} -> {lt}")
