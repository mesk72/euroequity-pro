import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

print("=== Righe totali per mercato (stima copertura reale) ===")
grand_total = 0
for ex in ALL_RANKED:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"1"})
    cr = r.headers.get("content-range","")
    count = cr.split("/")[-1] if "/" in cr else "?"
    # stima titoli coperti assumendo ~1260 giorni/titolo
    try:
        est_tickers = int(count) // 1260
    except:
        est_tickers = "?"
    print(f"  {ex}: righe={count}, stima_titoli_coperti~={est_tickers}")
    try:
        grand_total += int(count)
    except: pass

print(f"\nTotale righe in tutto prices_eod: {grand_total}")
print(f"Stima titoli totali coperti: ~{grand_total // 1260}")
