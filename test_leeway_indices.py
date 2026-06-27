import os, requests, time
from datetime import datetime, timedelta

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_10D     = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}
LEEWAY_SUFFIX = {
    "AS": ".AS", "MC": ".MC", "BR": ".BR", "LS": ".LS",
    "VI": ".VI", "HE": ".HE", "IR": ".IR", "AT": ".VI",
    "SWX": ".SW", "OM": ".ST", "NGM": ".ST", "OB": ".OL",
    "CPSE": ".CO", "AIM": ".AIM",
    "TSX": ".TO", "TSE": ".TSE", "SEHK": ".HK", "ASX": ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    return ticker.rstrip(".") + LEEWAY_SUFFIX.get(exchange, "")

print("TODAY:", TODAY, "FROM:", FROM_10D)

# Senza US — troppo lento, lo testiamo separatamente
EXCHANGES = [
    "AS","MC","BR","LS","VI","HE","IR",
    "SWX","OM","OB","CPSE",
    "TSX","TSE","SEHK","ASX",
]

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
    for s in stocks:
        lt = leeway_ticker(s["ticker"], exchange)
        url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
        try:
            r2 = requests.get(url, timeout=10)
            data = r2.json() if r2.status_code == 200 and isinstance(r2.json(), list) else []
            if data: ok.append(lt)
            else: empty.append((s["ticker"], lt))
        except: empty.append((s["ticker"], lt))
        time.sleep(0.15)

    print(f"{exchange}: {len(stocks)} — OK={len(ok)} VUOTI={len(empty)}")
    for tk, lt in empty:
        print(f"  {tk} -> {lt}")
