import os, requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_5D      = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

LEEWAY_SUFFIX = {
    "MIL": ".MI", "XETRA": ".XETRA", "PA": ".PA",
    "AS": ".AS", "MC": ".MC", "BR": ".BR",
    "LS": ".LS", "VI": ".VI", "HE": ".HE",
    "IR": ".IR", "AT": ".VI", "LSE": ".LSE",
    "AIM": ".AIM", "SWX": ".SW", "OM": ".ST",
    "NGM": ".ST", "OB": ".OL", "CPSE": ".CO",
    "TSE": ".TSE", "ASX": ".AU",
}

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}

def leeway_ticker(ticker, exchange, listing_exchange=None):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    # US: usa listing_exchange se disponibile
    if exchange == "US":
        if listing_exchange:
            le = listing_exchange.upper()
            if "NASDAQ" in le: return ticker + ".NASDAQ"
            if "NYSE" in le and "ARCA" in le: return ticker + ".AMEX"
            if "NYSE" in le: return ticker + ".NYSE"
            if "AMEX" in le or "AMERICAN" in le: return ticker + ".AMEX"
        return ticker + ".US"
    return ticker + LEEWAY_SUFFIX.get(exchange, "")

def test_ticker(args):
    ticker, exchange, listing_exchange = args
    lt = leeway_ticker(ticker, exchange, listing_exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=8)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return (ticker, exchange, lt, True, last.get("date"))
        return (ticker, exchange, lt, False, None)
    except:
        return (ticker, exchange, lt, False, None)

print("TODAY:", TODAY)

# Carica tutti i campi stocks per capire dove è la borsa di quotazione
r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "*", "exchange": "eq.US", "in_universe": "eq.true", "limit": "3"})
sample = r.json()
if isinstance(sample, list) and sample:
    print("Campi tabella stocks:", list(sample[0].keys()))
    print("Esempio:", sample[0])

# Test prime 50 per US, MIL, PA, XETRA
for exchange in ["US", "MIL", "PA", "XETRA"]:
    r2 = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "*", "exchange": f"eq.{exchange}",
                "in_universe": "eq.true", "limit": "50"})
    stocks = r2.json()
    if not isinstance(stocks, list): continue

    args = [(s["ticker"], exchange, s.get("listing_exchange") or s.get("market") or s.get("exchange_sub") or "") for s in stocks]
    
    ok = []; empty = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(test_ticker, a): a for a in args}
        for future in as_completed(futures):
            ticker, ex, lt, has_data, date = future.result()
            if has_data: ok.append((ticker, lt, date))
            else: empty.append((ticker, lt))

    print(f"\n{exchange}: OK={len(ok)} VUOTI={len(empty)}")
    for t, lt in empty:
        print(f"  !! {t} -> {lt}")
