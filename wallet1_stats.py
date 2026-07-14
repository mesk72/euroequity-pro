import os, requests, statistics
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/watchlist", headers=headers_r,
    params={"select":"ticker,exchange,wallet","wallet":"eq.0"})
wallet1 = r.json()
print(f"Titoli in Wallet 1: {len(wallet1)}")

caps = []
missing = []
for w in wallet1:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"mkt_cap","ticker":f"eq.{w['ticker']}","exchange":f"eq.{w['exchange']}"})
    d = r2.json()
    if d and d[0].get("mkt_cap") is not None:
        caps.append((w["ticker"], w["exchange"], d[0]["mkt_cap"]))
    else:
        missing.append(f"{w['ticker']}.{w['exchange']}")

print(f"\nTitoli con mkt_cap disponibile: {len(caps)}")
if missing:
    print(f"Titoli SENZA mkt_cap: {missing}")

values = [c[2] for c in caps]  # in milioni di $
if values:
    print(f"\nMedia: ${statistics.mean(values)/1000:,.2f}B")
    print(f"Mediana: ${statistics.median(values)/1000:,.2f}B")
    print(f"\nDettaglio (ordinato per market cap):")
    for t, ex, m in sorted(caps, key=lambda x: -x[2]):
        print(f"  {t}.{ex}: ${m/1000:,.2f}B")
