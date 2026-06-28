import os, requests
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

TARGET_DATE  = "2026-06-26"  # Ultima chiusura di borsa

EXCHANGES = ["MIL","XETRA","PA","LSE","OM","SWX","OB","AS","MC","BR",
             "CPSE","HE","VI","IR","LS","US","TSX","TSE","SEHK","ASX"]

print(f"Verifica qualita dati prezzi — target: {TARGET_DATE}")
print(f"{'Exchange':<8} {'Totale':>8} {'OK al 26/6':>11} {'Stale':>7} {'No Prezzi':>10}")
print("-" * 50)

stale_all = []

for ex in EXCHANGES:
    # Carica tutti i titoli in universe
    stocks = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": "eq." + ex, "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    ok = stale = no_price = 0
    stale_tickers = []

    for s in stocks:
        r2 = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date", "ticker": "eq." + s["ticker"],
                    "exchange": "eq." + ex, "order": "date.desc", "limit": "1"})
        row = r2.json()
        if not isinstance(row, list) or not row:
            no_price += 1
            stale_tickers.append((s["ticker"], "NO_DATA"))
        else:
            last = row[0]["date"]
            if last >= TARGET_DATE:
                ok += 1
            else:
                stale += 1
                stale_tickers.append((s["ticker"], last))

    print(f"{ex:<8} {len(stocks):>8} {ok:>11} {stale:>7} {no_price:>10}")
    stale_all.extend([(ex, tk, last) for tk, last in stale_tickers])

print(f"\nTOTALE STALE/NO DATA: {len(stale_all)}")
print("\nDettaglio titoli non aggiornati al 26/06/2026:")
print(f"{'Exchange':<8} {'Ticker':<15} {'Ultima Data':<12}")
print("-" * 38)
for ex, tk, last in sorted(stale_all):
    print(f"{ex:<8} {tk:<15} {last:<12}")
