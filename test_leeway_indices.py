import os, requests
from collections import Counter

SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Leggi yahoo_ticker per titoli US per capire il formato
all_us = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,yahoo_ticker", "exchange": "eq.US",
                "in_universe": "eq.true", "limit": "1000", "offset": str(offset)})
    batch = r.json()
    if not isinstance(batch, list) or not batch: break
    all_us.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Titoli US: {len(all_us)}")
print("\nPrimi 20 yahoo_ticker:")
for s in all_us[:20]:
    print(f"  ticker={s['ticker']} yahoo={s.get('yahoo_ticker')}")

# Conta suffissi yahoo_ticker
suffixes = Counter()
for s in all_us:
    yt = s.get("yahoo_ticker") or ""
    if "." in yt:
        suffixes[yt.split(".")[-1]] += 1
    else:
        suffixes["no_suffix"] += 1
print("\nSuffissi yahoo_ticker US:")
for suf, cnt in sorted(suffixes.items(), key=lambda x: -x[1]):
    print(f"  .{suf}: {cnt}")
