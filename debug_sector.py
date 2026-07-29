import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica ESATTA di come lo script costruisce by_exchange['ASX']
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker,primary_exchange", "in_universe": "eq.true",
                "exchange": "in.(TSE,SEHK,ASX,KRX,SGX)",
                "offset": str(offset), "limit": "1000"})
    if not r.text or r.text == "[]": break
    data = r.json()
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break

asx_tickers = [s["ticker"] for s in all_stocks if s["exchange"] == "ASX"]
print(f"Totale ASX in_universe: {len(asx_tickers)}")

# Trova il chunk (da 20) che contiene WES
CHUNK = 20
idx_wes = asx_tickers.index("WES") if "WES" in asx_tickers else -1
print(f"Posizione di WES nella lista: {idx_wes}")
chunk_start = (idx_wes // CHUNK) * CHUNK
chunk = asx_tickers[chunk_start:chunk_start+CHUNK]
print(f"Chunk contenente WES (posizioni {chunk_start}-{chunk_start+CHUNK}): {chunk}")

# Esegui la STESSA query esatta dello script per questo chunk
from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
    params={"select": "ticker,date,adj_close",
            "exchange": "eq.ASX",
            "ticker": "in.(" + ",".join(chunk) + ")",
            "date": "gte." + from_400d,
            "order": "ticker,date.desc",
            "limit": "1000", "offset": "0"})
print(f"\nHTTP status: {rp.status_code}")
batch = rp.json()
print(f"Righe totali restituite: {len(batch) if isinstance(batch,list) else 'ERRORE: ' + str(batch)}")
if isinstance(batch, list):
    tickers_returned = set(b["ticker"] for b in batch)
    print(f"Ticker DISTINTI restituiti: {sorted(tickers_returned)}")
    missing = [t for t in chunk if t not in tickers_returned]
    print(f"Ticker del chunk MANCANTI dalla risposta: {missing}")
    # Ultima data per ogni ticker restituito
    latest_per_ticker = {}
    for b in batch:
        if b["ticker"] not in latest_per_ticker or b["date"] > latest_per_ticker[b["ticker"]]:
            latest_per_ticker[b["ticker"]] = b["date"]
    print(f"Ultima data per ticker nel batch: {latest_per_ticker}")
