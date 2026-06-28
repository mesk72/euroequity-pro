import os, requests, time
from datetime import datetime, timedelta
from collections import defaultdict

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
    "US": ".US", "TSX": ".TO", "TSE": ".TSE", "SEHK": ".HK", "ASX": ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    return ticker.rstrip(".") + LEEWAY_SUFFIX.get(exchange, "")

print("TODAY:", TODAY, "FROM:", FROM_10D)
print("LEEWAY_KEY:", LEEWAY_KEY[:8] + "..." if LEEWAY_KEY else "MANCANTE!")

EXCHANGES = [
    "AS","MC","BR","LS","VI","HE","IR",
    "SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX",
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
print(f"Stima: {len(all_stocks)/2/60:.0f} minuti")

# Test primo ticker manualmente per verificare
t0, e0 = all_stocks[0]
lt0 = leeway_ticker(t0, e0)
url0 = LEEWAY_BASE + "/historicalquotes/" + lt0 + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
r0 = requests.get(url0, timeout=15)
print(f"\nTest primo ticker {lt0}: HTTP {r0.status_code} — {str(r0.text)[:100]}")

# Loop sequenziale semplice
empty = defaultdict(list)
ok = 0
for i, (ticker, exchange) in enumerate(all_stocks):
    lt = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_10D + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=15)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            ok += 1
        else:
            empty[exchange].append((ticker, lt, f"HTTP {r.status_code}"))
    except Exception as ex:
        empty[exchange].append((ticker, lt, str(ex)[:30]))
    time.sleep(0.5)
    if (i+1) % 500 == 0:
        print(f"  {i+1}/{len(all_stocks)} ok={ok} vuoti={sum(len(v) for v in empty.values())}")

print(f"\n=== RISULTATO ===")
print(f"OK: {ok}  VUOTI: {sum(len(v) for v in empty.values())}")
for ex in EXCHANGES:
    items = empty.get(ex, [])
    total_ex = sum(1 for t, e in all_stocks if e == ex)
    print(f"\n{ex}: {total_ex} — OK={total_ex-len(items)} VUOTI={len(items)}")
    for tk, lt, info in items:
        print(f"  {tk} -> {lt} ({info})")
