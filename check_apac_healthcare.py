import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

APAC = ["TSE","SEHK","ASX","KRX","SGX"]
rows = []
for ex in APAC:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,company","exchange":f"eq.{ex}","sector":"eq.Healthcare","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch:
            r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
                params={"select":"mkt_cap,mom12m","ticker":f"eq.{s['ticker']}","exchange":f"eq.{ex}"})
            d = r2.json()
            if d and d[0].get("mkt_cap") and d[0].get("mom12m") is not None:
                rows.append({"ticker":s["ticker"],"exchange":ex,"company":s["company"],"mkt_cap":d[0]["mkt_cap"],"mom12m":d[0]["mom12m"]})
        offset += 1000
        if len(batch) < 1000: break

rows.sort(key=lambda x: -x["mkt_cap"])
print(f"Titoli Healthcare APAC con dati: {len(rows)}")
total_mkt = sum(r["mkt_cap"] for r in rows)
ws = sum(r["mkt_cap"]*r["mom12m"] for r in rows)
print(f"Media ponderata 12M (cap attuale): {100*ws/total_mkt:.2f}%")
print("\nTop 10 per market cap:")
for r in rows[:10]:
    print(f"  {r['ticker']} ({r['company'][:30]}): mktcap={r['mkt_cap']:.1f}B mom12m={r['mom12m']*100:.1f}%")
print("\nPeggiori 5 per mom12m:")
for r in sorted(rows, key=lambda x: x["mom12m"])[:5]:
    print(f"  {r['ticker']} ({r['company'][:30]}): mktcap={r['mkt_cap']:.1f}B mom12m={r['mom12m']*100:.1f}%")
