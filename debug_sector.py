import os, requests, time
from datetime import datetime, timedelta
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica esatta di by_exchange["ASX"]: stessa query, stesso ordine
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange", "in_universe": "eq.true",
                "exchange": "eq.ASX", "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
tickers = [s["ticker"] for s in all_stocks]
print(f"ASX universo: {len(tickers)} titoli")

CHUNK = 20
from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
found_wes = False
for i in range(0, len(tickers), CHUNK):
    chunk = tickers[i:i+CHUNK]
    if "WES" in chunk:
        found_wes = True
        print(f"\nWES e' nel chunk#{i//CHUNK}: {chunk}")
        # Replica ESATTA della paginazione, SENZA retry (comportamento vecchio) per vedere dove si rompe
        offset_p = 0
        page_num = 0
        wes_found_in_pages = False
        while True:
            rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "ticker,date,adj_close",
                        "exchange": "eq.ASX",
                        "ticker": "in.(" + ",".join(chunk) + ")",
                        "date": "gte." + from_400d,
                        "order": "ticker,date.desc",
                        "limit": "1000", "offset": str(offset_p)})
            page_num += 1
            batch = rp.json()
            if not isinstance(batch, list):
                print(f"  Pagina {page_num} (offset={offset_p}): FALLITA HTTP={rp.status_code} body={str(batch)[:200]}")
                break
            wes_rows_here = [d for d in batch if d["ticker"] == "WES"]
            print(f"  Pagina {page_num} (offset={offset_p}): {len(batch)} righe totali, {len(wes_rows_here)} di WES"
                  + (f" (piu' recente: {max(d['date'] for d in wes_rows_here)})" if wes_rows_here else ""))
            if wes_rows_here: wes_found_in_pages = True
            if not batch: break
            offset_p += 1000
            if len(batch) < 1000: break
        print(f"WES trovato nella lettura completa del chunk: {wes_found_in_pages}")
        break
if not found_wes:
    print("WES non e' nell'universo ASX attuale (in_universe potrebbe essere false)")
