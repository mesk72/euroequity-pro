import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json", "Prefer":"resolution=merge-duplicates,return=minimal"}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

universe_keys = set()
for ex in ALL_RANKED:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: universe_keys.add((s["ticker"], s["exchange"]))
        offset += 1000
        if len(batch) < 1000: break

print(f"Universo totale (in_universe=true): {len(universe_keys)}")

all_fund = []
for ex in ALL_RANKED:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,mkt_cap","exchange":f"eq.{ex}","mkt_cap":"not.is.null","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_fund.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

filtered = [f for f in all_fund if (f["ticker"], f["exchange"]) in universe_keys]
print(f"Con mkt_cap e in_universe: {len(filtered)}")

top500 = sorted(filtered, key=lambda x: -(x["mkt_cap"] or -1))[:500]
print(f"Top 500 selezionati: {len(top500)}")

rows = [{"ticker": f["ticker"], "exchange": f["exchange"]} for f in top500]
for i in range(0, len(rows), 200):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/top500_universe", headers=headers_up, json=rows[i:i+200])
    print(f"  batch {i}: HTTP {r.status_code}")

# Verifica finale
rv = requests.get(f"{SUPABASE_URL}/rest/v1/top500_universe", headers={**headers_r,"Prefer":"count=exact"}, params={"select":"ticker","limit":"1"})
print("Righe totali nella tabella:", rv.headers.get("content-range"))
