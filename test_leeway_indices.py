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

# Rate limiter: max 7 req/sec
_lock = threading.Lock()
_last_call = [0.0]

def rate_limited_get(url):
    with _lock:
        now = time.time()
        elapsed = now - _last_call[0]
        if elapsed < 1/7:
            time.sleep(1/7 - elapsed)
        _last_call[0] = time.time()
    return requests.get(url, timeout=10)

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

def test_one(args):
    ticker, exchange = args
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
    try:
        r = rate_limited_get(url)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            last = sorted(data, key=lambda x: x["date"])[-1]
            return ticker, exchange, lt, True, last.get("date")
        return ticker, exchange, lt, False, None
    except:
        return ticker, exchange, lt, False, None

print("TODAY:", TODAY, "FROM:", FROM_10D)

EXCHANGES = [
    "AS","MC","BR","LS","VI","HE","IR",
    "SWX","OM","OB","CPSE",
    "TSX","TSE","SEHK","ASX",
]

# Carica tutti i titoli
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
print(f"Stima: {len(all_stocks)/7/60:.1f} minuti a 7 req/sec")

# Test con 7 thread — rispetta rate limit 7 req/sec
results = []
with ThreadPoolExecutor(max_workers=7) as executor:
    results = list(executor.map(test_one, all_stocks))

# Stampa vuoti per exchange
from collections import defaultdict
by_ex = defaultdict(list)
ok = 0
for ticker, exchange, lt, has_data, date in results:
    if has_data: ok += 1
    else: by_ex[exchange].append((ticker, lt))

print(f"\n=== RISULTATO ===")
print(f"OK: {ok}  VUOTI: {sum(len(v) for v in by_ex.values())}")
for ex in EXCHANGES:
    items = by_ex.get(ex, [])
    total_ex = sum(1 for t, e, l, h, d in results if e == ex)
    print(f"\n{ex}: {total_ex} — OK={total_ex-len(items)} VUOTI={len(items)}")
    for tk, lt in items:
        print(f"  {tk} -> {lt}")
