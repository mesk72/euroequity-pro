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

# Suffissi da testare per ogni exchange
# Formato: exchange -> lista di suffissi alternativi da provare
SUFFIXES = {
    "MIL":   [".MI", ".MIL", ".BIT"],
    "XETRA": [".XETRA", ".DE", ".F"],
    "PA":    [".PA", ".EUR"],
    "AS":    [".AS", ".AMS"],
    "MC":    [".MC", ".ES"],
    "BR":    [".BR", ".BRU"],
    "LS":    [".LS", ".LIS"],
    "VI":    [".VI", ".VIE"],
    "HE":    [".HE", ".HSE"],
    "IR":    [".IR", ".ISE"],
    "AT":    [".AT"],
    "LSE":   [".LSE", ".L", ".LON"],
    "AIM":   [".AIM", ".L"],
    "SWX":   [".SW", ".SWX", ".VX"],
    "OM":    [".ST", ".OM"],
    "NGM":   [".ST", ".NGM"],
    "OB":    [".OL", ".OB"],
    "CPSE":  [".CO", ".CPH"],
    "US":    [".US", ".NYSE", ".NASDAQ"],
    "TSX":   [".TO", ".TSX"],
    "TSE":   [".TSE", ".T", ".JP"],
    "SEHK":  [".HK"],
    "ASX":   [".AU", ".AX", ".ASX"],
}

def test_ticker_formats(ticker, exchange):
    suffixes = SUFFIXES.get(exchange, [])
    for suffix in suffixes:
        if exchange == "SEHK":
            lt = ticker.zfill(4) + suffix
        else:
            lt = ticker + suffix
        url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
        try:
            r = requests.get(url, timeout=8)
            data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
            if data:
                last = sorted(data, key=lambda x: x["date"])[-1]
                return (ticker, exchange, lt, last.get("date"), last.get("close"))
        except: pass
    return (ticker, exchange, None, None, None)

# Carica primi 20 per ogni exchange
print("TODAY:", TODAY)
all_stocks = []
for ex_filter in ["not.in.(US,TSX,TSE,SEHK,ASX)", "in.(US,TSX)", "in.(TSE,SEHK,ASX)"]:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange", "in_universe": "eq.true",
                "exchange": ex_filter, "limit": "1000", "order": "exchange,ticker"})
    batch = r.json()
    if isinstance(batch, list):
        from collections import defaultdict
        by_ex = defaultdict(list)
        for s in batch:
            by_ex[s["exchange"]].append(s["ticker"])
        for ex, tickers in by_ex.items():
            for t in tickers[:20]:
                all_stocks.append((t, ex))

print(f"Testando {len(all_stocks)} titoli (20 per exchange)...")

results = []
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(test_ticker_formats, t, ex): (t, ex) for t, ex in all_stocks}
    for future in as_completed(futures):
        results.append(future.result())

# Stampa risultati per exchange
from collections import defaultdict
by_ex = defaultdict(list)
for ticker, exchange, lt, date, close in results:
    by_ex[exchange].append((ticker, lt, date, close))

for ex in sorted(by_ex.keys()):
    items = by_ex[ex]
    ok = [(t, lt, d, c) for t, lt, d, c in items if lt]
    fail = [(t, lt, d, c) for t, lt, d, c in items if not lt]
    print(f"\n{ex}: {len(ok)}/20 OK, {len(fail)} vuoti")
    if fail:
        for t, lt, d, c in fail:
            print(f"  VUOTO: {t}")
    if ok:
        # Mostra suffisso che funziona
        suffix_used = set(lt.replace(t, "") for t, lt, d, c in ok if lt)
        print(f"  Suffisso OK: {suffix_used}")
        print(f"  Ultima data: {ok[0][2]}")
