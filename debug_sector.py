import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

TODAY = datetime.now().strftime("%Y-%m-%d")
END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

# Prendo 150 titoli VERI dall'universo US (stesso chunk size del vero script)
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"150","order":"ticker"})
test_tickers = [s["ticker"] for s in r.json()]
print(f"Campione: {len(test_tickers)} titoli reali")

# Data globale mercato (stessa logica del vero script)
rg = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date","exchange":"eq.US","order":"date.desc","limit":"1"})
global_last = rg.json()[0]["date"]
print(f"Data globale mercato: {global_last}")
start_dt = (datetime.strptime(global_last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
print(f"start_dt: {start_dt}, end: {END_FOR_DOWNLOAD}")

print("\nScarico...")
data_yf = yf.download(tickers=" ".join(test_tickers), start=start_dt, end=END_FOR_DOWNLOAD,
                       interval="1d", auto_adjust=True, progress=False, threads=True)
print(f"Scaricato: empty={data_yf.empty}, shape={data_yf.shape}")

if isinstance(data_yf.columns, pd.MultiIndex):
    closes = data_yf["Close"] if "Close" in data_yf.columns.get_level_values(0) else data_yf.xs("Close", axis=1, level=1)
else:
    closes = data_yf if "Close" not in data_yf.columns else data_yf[["Close"]]

print(f"closes shape: {closes.shape}, colonne trovate: {len(closes.columns)}/{len(test_tickers)}")

# Prova la scrittura per i primi 5 titoli
price_buf = []
for tk in test_tickers[:5]:
    if tk not in closes.columns:
        print(f"  {tk}: MANCA in closes!")
        continue
    vals = closes[tk].dropna()
    print(f"  {tk}: {len(vals)} righe scaricate, ultima={vals.index[-1].strftime('%Y-%m-%d') if len(vals) else 'N/A'}")
    for date_idx, price in vals.items():
        date_str = date_idx.strftime("%Y-%m-%d")
        if date_str <= global_last: continue
        price_buf.append({"ticker": tk, "exchange": "US", "date": date_str, "adj_close": round(float(price), 6)})

print(f"\nRighe da scrivere (primi 5 titoli): {len(price_buf)}")
if price_buf:
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=price_buf)
    print(f"Scrittura: HTTP {r2.status_code}, {r2.text[:300]}")
