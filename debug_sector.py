import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

all_rows = []
for ex in ALL_RANKED:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,mkt_cap","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_rows.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

print(f"Totale righe fundamentals in tutti i mercati: {len(all_rows)}")
with_cap = [r for r in all_rows if r.get("mkt_cap") is not None]
print(f"Con mkt_cap non nullo: {len(with_cap)}")
print(f"Senza mkt_cap (esclusi dal calcolo top 500): {len(all_rows) - len(with_cap)}")
