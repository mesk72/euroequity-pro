import os, requests, time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_10D     = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Rate limiter: 2 req/sec come raccomandato da Leeway
_lock = threading.Lock()
_last_call = [0.0]

def rate_limited_get(url):
    with _lock:
        now = time.time()
        elapsed = now - _last_call[0]
        if elapsed < 0.5:  # 1/2 sec = 2 req/sec
            time.sleep(0.5 - elapsed)
        _last_call[0] = time.time()
    return requests.get(url, timeout=15)

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}
LEEWAY_SUFFIX = {
    "AS": ".AS", "MC": ".MC", "BR": ".BR", "LS": ".LS",
    "VI": ".VI", "HE": ".HE", "IR": ".IR", "AT": ".VI",
    "SWX": ".SW", "OM": ".ST", "NGM": ".ST", "OB": ".OL",
    "CPSE": ".CO", "AIM": ".AIM",
    "US": ".US", "TSX": ".TO", "TSE": ".TSE", "SEHK": ".HK", "ASX": ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    return ticker.rstrip(".") + LEEWAY_SUFFIX.get(exchange, "")

def test_one(args):
    ticker, exchange = args
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
    try:
        r = rate_limited_get(url)
        if r.status_code != 200:
            return ticker, exchange, lt, False, f"HTTP {r.status_code}"
        data = r.json() if isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return ticker, exchange, lt, True, last.get("date")
        return ticker, exchange, lt, False, "empty"
    except Exception as e:
        return ticker, exchange, lt, False, str(e)[:30]

print("TODAY:", TODAY, "FROM:", FROM_10D)

EXCHANGES = [
    "AS","MC","BR","LS","VI","HE","IR",
    "SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX",
]

all_stocks = []
for exchange in EXCHANGES:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": f"eq.{exchange}",
                    "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_stocks.extend([(s["ticker"], exchange) for s in batch])
        offset += 1000
        if len(batch) < 1000: break

print(f"Totale: {len(all_stocks)} titoli")
print(f"Stima: {len(all_stocks)/2/60:.1f} minuti a 2 req/sec")

# 2 thread — rispetta 2 req/sec grazie al rate limiter
with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(test_one, all_stocks))

from collections import defaultdict
by_ex = defaultdict(list)
ok = 0
for ticker, exchange, lt, has_data, info in results:
    if has_data: ok += 1
    else: by_ex[exchange].append((ticker, lt, info))

print(f"\n=== RISULTATO ===")
print(f"OK: {ok}  VUOTI: {sum(len(v) for v in by_ex.values())}")
for ex in EXCHANGES:
    items = by_ex.get(ex, [])
    total_ex = sum(1 for t, e, l, h, i in results if e == ex)
    print(f"\n{ex}: {total_ex} — OK={total_ex-len(items)} VUOTI={len(items)}")
    for tk, lt, info in items:
        print(f"  {tk} -> {lt} ({info})")
