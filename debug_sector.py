import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

def fetch_all(table, params_extra):
    rows = []
    offset = 0
    while True:
        p = {**params_extra, "limit":"1000", "offset":str(offset)}
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_r, params=p)
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        rows.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return rows

universe_keys = set()
all_fund = []
for ex in ALL_RANKED:
    us = fetch_all("stocks", {"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true"})
    for s in us: universe_keys.add(f"{s['ticker']}.{s['exchange']}")
    fund = fetch_all("fundamentals", {"select":"ticker,exchange,mkt_cap","exchange":f"eq.{ex}","mkt_cap":"not.is.null"})
    all_fund.extend(fund)

filtered = [f for f in all_fund if f"{f['ticker']}.{f['exchange']}" in universe_keys]
top500 = sorted(filtered, key=lambda x: -(x['mkt_cap'] or -1))[:500]
top500_keys = set(f"{f['ticker']}.{f['exchange']}" for f in top500)

print(f"Totale candidati con in_universe + mkt_cap: {len(filtered)}")
print(f"Top 500 calcolati: {len(top500)}")
print(f"IBM.US e' nella top 500? {'IBM.US' in top500_keys}")

# Trova la posizione esatta di IBM nella classifica
sorted_all = sorted(filtered, key=lambda x: -(x['mkt_cap'] or -1))
for i, f in enumerate(sorted_all):
    if f['ticker'] == 'IBM' and f['exchange'] == 'US':
        print(f"Posizione di IBM per market cap: #{i+1}")
        break
