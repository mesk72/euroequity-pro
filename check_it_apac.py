import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

APAC = ["TSE","SEHK","ASX","KRX","SGX"]
all_it = []
for ex in APAC:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,company,sector","exchange":f"eq.{ex}","sector":"eq.Information Technology","in_universe":"eq.true","limit":"1000"})
    all_it.extend(r.json())
print(f"Titoli IT APAC in universo: {len(all_it)}")

rows = []
for s in all_it:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"mkt_cap,mom12m","ticker":f"eq.{s['ticker']}","exchange":f"eq.{s['exchange']}"})
    d = r.json()
    if d and d[0].get("mkt_cap") and d[0].get("mom12m") is not None:
        rows.append({"ticker": s["ticker"], "company": s["company"], "mkt_cap": d[0]["mkt_cap"], "mom12m": d[0]["mom12m"]})

rows.sort(key=lambda x: -x["mkt_cap"])
print(f"\nTop 10 per market cap (quelli che pesano di piu' nella media):")
total_mkt = sum(r["mkt_cap"] for r in rows)
weighted_sum = sum(r["mkt_cap"]*r["mom12m"] for r in rows)
for r in rows[:10]:
    print(f"  {r['ticker']} ({r['company'][:30]}): mktcap={r['mkt_cap']:.1f}B mom12m={r['mom12m']*100:.1f}%")
print(f"\nTotale mkt cap (tutti i {len(rows)} con dati): {total_mkt:.1f}B")
print(f"Media ponderata mom12m manuale: {100*weighted_sum/total_mkt:.2f}%")
