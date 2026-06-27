import os, requests
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

def test_ticker(args):
    ticker, exchange = args
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return (ticker, exchange, lt, True, last.get("date"))
        return (ticker, exchange, lt, False, None)
    except:
        return (ticker, exchange, lt, False, None)

print("TODAY:", TODAY)

EXCHANGES = ["US", "MIL", "XETRA", "PA", "LSE"]

for exchange in EXCHANGES:
    # Carica tutti i titoli in universe per questo exchange
    stocks = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": f"eq.{exchange}",
                    "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    # Test sequenziale — affidabile, no rate limit
    import time
    ok = []; empty = []
    for s in stocks:
        ticker, ex, lt, has_data, date = test_ticker((s["ticker"], s["exchange"]))
        if has_data: ok.append((ticker, lt, date))
        else: empty.append((ticker, lt))
        time.sleep(0.05)

    print(f"\n{exchange}: {len(stocks)} titoli — OK={len(ok)} VUOTI={len(empty)}")
    for tk, lt in empty:
        print(f"  {tk} -> {lt}")
