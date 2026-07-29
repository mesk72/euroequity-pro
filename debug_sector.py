import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica ESATTA di come lo script costruisce by_exchange['ASX']
all_stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
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
print(f"Totale ASX in_universe=true: {len(asx_tickers)}")
print(f"WES presente in lista? {'WES' in asx_tickers}")
if "WES" in asx_tickers:
    idx = asx_tickers.index("WES")
    chunk_idx = idx // 20
    chunk = asx_tickers[chunk_idx*20:(chunk_idx+1)*20]
    print(f"WES e' in posizione {idx}, chunk #{chunk_idx}: {chunk}")

    from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
    params = {"select": "ticker,date,adj_close",
              "exchange": "eq.ASX",
              "ticker": "in.(" + ",".join(chunk) + ")",
              "date": "gte." + from_400d,
              "order": "ticker,date.desc",
              "limit": "1000", "offset": "0"}
    print("\nURL params:", params)
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r, params=params)
    print(f"\nStatus: {rp.status_code}")
    batch = rp.json()
    print(f"Righe totali tornate: {len(batch) if isinstance(batch, list) else 'ERRORE: ' + str(batch)}")
    if isinstance(batch, list):
        tickers_in_response = set(row["ticker"] for row in batch)
        print(f"Ticker presenti nella risposta: {sorted(tickers_in_response)}")
        missing = set(chunk) - tickers_in_response
        print(f"Ticker MANCANTI dalla risposta: {sorted(missing)}")
        wes_rows = [row for row in batch if row["ticker"] == "WES"]
        print(f"Righe per WES specificamente: {len(wes_rows)}")
        print(wes_rows[:3])
else:
    print("WES non e' in_universe=true! Ecco perche' non viene processato.")
