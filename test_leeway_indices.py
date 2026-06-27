import os, requests, time
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
TODAY        = datetime.now().strftime("%Y-%m-%d")
FROM_5D      = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

LEEWAY_SUFFIX = {
    "MIL": ".MI", "XETRA": ".XETRA", "PA": ".PA", "AS": ".AS",
    "MC": ".MC", "BR": ".BR", "LS": ".LS", "VI": ".VI",
    "HE": ".HE", "IR": ".IR", "AT": ".AT", "LSE": ".LSE",
    "AIM": ".AIM", "SWX": ".SW", "OM": ".ST", "NGM": ".ST",
    "OB": ".OL", "CPSE": ".CO",
    "US": ".US", "TSX": ".TO",
    "TSE": ".TSE", "SEHK": ".HK", "ASX": ".AU",
}

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    return ticker + LEEWAY_SUFFIX.get(exchange, "")

def test_ticker(args):
    ticker, exchange = args
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=8)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        return (ticker, exchange, lt, len(data) > 0)
    except:
        return (ticker, exchange, lt, False)

print("TODAY:", TODAY)
print("Carico universo EU (no US/APAC per ora)...")

all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange", "in_universe": "eq.true",
                "exchange": "not.in.(US,TSX,TSE,SEHK,ASX)",
                "limit": "1000", "offset": str(offset)})
    batch = r.json()
    if not isinstance(batch, list) or not batch: break
    all_stocks.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Totale EU: {len(all_stocks)} titoli")
print("Test con 30 thread paralleli...")

empty = []
ok = 0
args = [(s["ticker"], s["exchange"]) for s in all_stocks]

with ThreadPoolExecutor(max_workers=30) as executor:
    futures = {executor.submit(test_ticker, a): a for a in args}
    done = 0
    for future in as_completed(futures):
        ticker, exchange, lt, has_data = future.result()
        done += 1
        if has_data:
            ok += 1
        else:
            empty.append((exchange, ticker, lt))
        if done % 200 == 0:
            print(f"  {done}/{len(args)} ok={ok} empty={len(empty)}")

print(f"\n=== RISULTATO EU ===")
print(f"OK: {ok}  VUOTI: {len(empty)}")
by_ex = defaultdict(list)
for ex, tk, lt in empty:
    by_ex[ex].append((tk, lt))
for ex, items in sorted(by_ex.items()):
    print(f"\n{ex} ({len(items)} vuoti):")
    for tk, lt in items:
        print(f"  {tk} -> {lt}")
