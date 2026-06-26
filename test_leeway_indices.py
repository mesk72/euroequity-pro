import os, requests, time
from datetime import datetime, timedelta

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
print("Carico universo dal DB...")

# Leggi tutti i ticker in_universe
all_stocks = []
for exchange_filter, label in [
    ("not.in.(US,TSX,TSE,SEHK,ASX)", "EU"),
    ("in.(US,TSX)", "US+CA"),
    ("in.(TSE,SEHK,ASX)", "APAC"),
]:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": exchange_filter, "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for s in batch: s["region"] = label
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

print(f"Totale titoli: {len(all_stocks)}")
print("Test Leeway in corso (campione 5 per exchange)...\n")

# Testa 5 titoli per exchange per velocità
from collections import defaultdict
by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s["exchange"]].append(s)

empty = []
ok_count = 0

for exchange, stocks in sorted(by_exchange.items()):
    sample = stocks[:10]  # testa primi 10 per exchange
    empty_ex = []
    for s in sample:
        ticker = s["ticker"]
        lt = leeway_ticker(ticker, exchange)
        url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5D + "&to=" + TODAY
        r = requests.get(url, timeout=8)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if data:
            ok_count += 1
        else:
            empty_ex.append((ticker, lt))
        time.sleep(0.05)
    
    if empty_ex:
        print(f"!! {exchange}: {len(empty_ex)}/{len(sample)} vuoti")
        for t, lt in empty_ex:
            print(f"   {t} → {lt}")
    else:
        last_date = sorted(data, key=lambda x: x["date"])[-1]["date"] if data else "?"
        print(f"OK {exchange}: tutti ok (ultimo: {last_date})")

print(f"\nOK: {ok_count} vuoti: {len(empty)}")
