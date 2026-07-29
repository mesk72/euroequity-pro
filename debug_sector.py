import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# 1) Prendi la lista ASX esatta usata dallo script (stessa query, stesso ordine)
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange", "in_universe": "eq.true",
                "exchange": "in.(TSE,SEHK,ASX,KRX,SGX)",
                "order": "ticker.asc", "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break

asx_tickers = [s["ticker"] for s in all_stocks if s["exchange"] == "ASX"]
print(f"Universo ASX: {len(asx_tickers)} titoli")

# 2) Replica ESATTA della lettura a chunk di 20 dello step 3
CHUNK = 20
from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
found_tickers = set()
for i in range(0, len(asx_tickers), CHUNK):
    chunk = asx_tickers[i:i+CHUNK]
    offset_p = 0
    while True:
        rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "ticker,date,adj_close",
                    "exchange": "eq.ASX",
                    "ticker": "in.(" + ",".join(chunk) + ")",
                    "date": "gte." + from_400d,
                    "order": "ticker,date.desc",
                    "limit": "1000", "offset": str(offset_p)})
        batch = rp.json()
        if not isinstance(batch, list) or not batch:
            break
        for d in batch:
            found_tickers.add(d["ticker"])
        offset_p += 1000
        if len(batch) < 1000: break

missing = sorted(set(asx_tickers) - found_tickers)
print(f"Trovati nella lettura a chunk: {len(found_tickers)} titoli distinti")
print(f"Mancanti: {len(missing)} -> {missing[:30]}")

# 3) Per 3 titoli mancanti, query DIRETTA a singolo ticker (bypassando i chunk)
print("\n=== Verifica diretta per singoli titoli mancanti ===")
for tk in missing[:5]:
    rd = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":"eq.ASX",
                "order":"date.desc","limit":"3"})
    print(f"{tk}: {rd.json()}")
