import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

TODAY = datetime.now().strftime("%Y-%m-%d")
END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
print(f"Oggi: {TODAY}, end download: {END_FOR_DOWNLOAD}")

test_tickers = ["AAPL", "MSFT", "NVDA"]
last_dates = {}
for tk in test_tickers:
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":"eq.US","order":"date.desc","limit":"1"})
    row = rp.json()
    last_dates[tk] = row[0]["date"] if row else "2020-01-01"
    print(f"{tk}: ultima data nel DB = {last_dates[tk]}")

start_dt = min(last_dates.values())
start_dt = (datetime.strptime(start_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
print(f"\nstart_dt: {start_dt}")

data_yf = yf.download(tickers=" ".join(test_tickers), start=start_dt, end=END_FOR_DOWNLOAD,
                       interval="1d", auto_adjust=True, progress=False, threads=True)
print(f"Scaricato, empty={data_yf.empty}, shape={data_yf.shape}")
print(f"Tipo colonne: {type(data_yf.columns)}")
if isinstance(data_yf.columns, pd.MultiIndex):
    print(f"Livello 0: {list(data_yf.columns.get_level_values(0).unique())}")

if len(test_tickers) == 1:
    closes = data_yf[["Close"]].rename(columns={"Close": test_tickers[0]})
elif isinstance(data_yf.columns, pd.MultiIndex):
    if "Close" in data_yf.columns.get_level_values(0):
        closes = data_yf["Close"]
    elif "Close" in data_yf.columns.get_level_values(1):
        closes = data_yf.xs("Close", axis=1, level=1)
    else:
        closes = None
elif "Close" in data_yf.columns:
    closes = data_yf[["Close"]].rename(columns={"Close": test_tickers[0]})
else:
    closes = None

print(f"\ncloses e' None? {closes is None}")
if closes is not None:
    print(f"closes.columns: {list(closes.columns)}")
    for tk in test_tickers:
        if tk in closes.columns:
            print(f"\n{tk} ultimi valori:")
            print(closes[tk].dropna().tail(5))
        else:
            print(f"\n{tk} NON in closes.columns!")
