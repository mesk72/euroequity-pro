import os, requests
from collections import Counter

SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== CONTEGGIO TITOLI IN UNIVERSE PER EXCHANGE ===")

# Leggi TUTTI i titoli in universe con paginazione
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker",
                "in_universe": "eq.true",
                "limit": "1000", "offset": str(offset)})
    batch = r.json()
    if not isinstance(batch, list) or not batch: break
    all_stocks.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Totale in_universe=true: {len(all_stocks)}")
counts = Counter(s["exchange"] for s in all_stocks)
for ex, cnt in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {ex}: {cnt}")

# Raggruppamenti
eu_ex = {"MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","AT","LSE","AIM","SWX","OM","NGM","OB","CPSE"}
eu = sum(cnt for ex, cnt in counts.items() if ex in eu_ex)
us = counts.get("US", 0)
tsx = counts.get("TSX", 0)
tse = counts.get("TSE", 0)
sehk = counts.get("SEHK", 0)
asx = counts.get("ASX", 0)

print(f"\nRiepilogo:")
print(f"  EU totale: {eu}")
print(f"  US: {us}")
print(f"  TSX (Canada): {tsx}")
print(f"  TSE (Giappone): {tse}")
print(f"  SEHK (HK): {sehk}")
print(f"  ASX (Australia): {asx}")
print(f"  APAC totale: {tse+sehk+asx}")

# Verifica yahoo_ticker per titoli US
us_stocks = [s for s in all_stocks if s["exchange"] == "US"]
with_yahoo = [s for s in us_stocks if s.get("yahoo_ticker")]
print(f"\nUS titoli: {len(us_stocks)}")
print(f"US con yahoo_ticker: {len(with_yahoo)}")
print(f"US senza yahoo_ticker: {len(us_stocks)-len(with_yahoo)}")
if us_stocks:
    print(f"Esempi: {[s['ticker'] for s in us_stocks[:10]]}")
