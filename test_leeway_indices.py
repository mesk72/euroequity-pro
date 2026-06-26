import os, requests, time
from datetime import datetime, timedelta
from collections import defaultdict

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

print("TODAY:", TODAY)
print("Carico universo...")

all_stocks = []
for exchange_filter in ["not.in.(US,TSX,TSE,SEHK,ASX)", "in.(US,TSX)", "in.(TSE,SEHK,ASX)"]:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": exchange_filter, "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

print(f"Totale: {len(all_stocks)} titoli")
print("Test in corso...\n")

empty = []
ok = 0
for i, s in enumerate(all_stocks):
    ticker   = s["ticker"]
    exchange = s["exchange"]
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=8)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            ok += 1
        else:
            empty.append((exchange, ticker, lt))
    except:
        empty.append((exchange, ticker, lt + " [timeout]"))
    if i % 500 == 0: print(f"  {i}/{len(all_stocks)} ok={ok} empty={len(empty)}")
    time.sleep(0.05)

print(f"\n=== RISULTATO ===")
print(f"OK: {ok}  VUOTI: {len(empty)}")
print()
by_ex = defaultdict(list)
for ex, tk, lt in empty:
    by_ex[ex].append((tk, lt))
for ex, items in sorted(by_ex.items()):
    print(f"\n{ex} ({len(items)} vuoti):")
    for tk, lt in items:
        print(f"  {tk} → {lt}")
