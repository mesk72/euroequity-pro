import os, requests
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

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}

LEEWAY_SUFFIX = {
    "MIL": ".MI", "XETRA": ".XETRA", "PA": ".PA",
    "AS": ".AS", "MC": ".MC", "BR": ".BR",
    "LS": ".LS", "VI": ".VI", "HE": ".HE",
    "IR": ".IR", "AT": ".VI", "LSE": ".LSE",
    "AIM": ".AIM", "SWX": ".SW", "OM": ".ST",
    "NGM": ".ST", "OB": ".OL", "CPSE": ".CO",
    "US": ".US", "TSX": ".TO",
    "TSE": ".TSE", "ASX": ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "CPSE": return ticker.replace(" ", "-") + ".CO"
    if exchange == "TSX":  return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":   return ticker.replace(".", "") + ".BR"
    return ticker + LEEWAY_SUFFIX.get(exchange, "")

def test_ticker(args):
    ticker, exchange = args
    lt = leeway_ticker(ticker, exchange)
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
all_stocks = []
for ex_filter, label in [
    ("not.in.(US,TSX,TSE,SEHK,ASX)", "EU"),
    ("in.(US,TSX)", "US+CA"),
    ("in.(TSE,SEHK,ASX)", "APAC"),
]:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": ex_filter, "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"{label}: {len([s for s in all_stocks])} totale")

print(f"Totale: {len(all_stocks)} titoli — test con 50 thread...")

empty = []; ok = 0
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(test_ticker, (s["ticker"], s["exchange"])): s for s in all_stocks}
    done = 0
    for future in as_completed(futures):
        ticker, exchange, lt, has_data, date = future.result()
        done += 1
        if has_data: ok += 1
        else: empty.append((exchange, ticker, lt))
        if done % 1000 == 0: print(f"  {done}/{len(all_stocks)} ok={ok} empty={len(empty)}")

print(f"\n=== RISULTATO FINALE ===")
print(f"OK: {ok}  VUOTI: {len(empty)}")
by_ex = defaultdict(list)
for ex, tk, lt in empty: by_ex[ex].append((tk, lt))
for ex in sorted(by_ex.keys()):
    items = by_ex[ex]
    print(f"\n{ex} ({len(items)} vuoti):")
    for tk, lt in items:
        print(f"  {tk} -> {lt}")
