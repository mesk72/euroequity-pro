import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Prendo il chunk REALE di 150 titoli TSE che include 7203 (in ordine come nello script)
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.TSE","in_universe":"eq.true","limit":"1000","order":"ticker"})
all_tse = [s["ticker"] for s in r.json()]
print(f"Totale TSE: {len(all_tse)}")

# Trovo in quale chunk da 150 cade 7203
idx_7203 = all_tse.index("7203") if "7203" in all_tse else -1
idx_9984 = all_tse.index("9984") if "9984" in all_tse else -1
print(f"7203 e' all'indice {idx_7203} (chunk {idx_7203//150})")
print(f"9984 e' all'indice {idx_9984} (chunk {idx_9984//150})")

chunk_start = (idx_7203 // 150) * 150
chunk = all_tse[chunk_start:chunk_start+150]
print(f"\nChunk contiene 7203? {'7203' in chunk}")
print(f"Dimensione chunk: {len(chunk)}")

ytickers = [tk + ".T" for tk in chunk]
data_yf = yf.download(tickers=" ".join(ytickers), start="2026-07-22", end="2026-07-29",
                       interval="1d", auto_adjust=True, progress=False, threads=True)
print(f"\nScaricato: empty={data_yf.empty}, shape={data_yf.shape}")
print(f"Tipo colonne: {type(data_yf.columns)}")

if isinstance(data_yf.columns, pd.MultiIndex):
    closes = data_yf["Close"] if "Close" in data_yf.columns.get_level_values(0) else data_yf.xs("Close", axis=1, level=1)
else:
    closes = data_yf

print(f"'7203.T' in closes.columns? {'7203.T' in closes.columns}")
if '7203.T' in closes.columns:
    print(closes['7203.T'].dropna().tail(5))
else:
    print("colonne disponibili (prime 10):", list(closes.columns)[:10])
