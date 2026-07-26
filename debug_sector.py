import os, requests, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"150","order":"ticker"})
test_tickers = [s["ticker"] for s in r.json()]
print(f"Campione: {len(test_tickers)} titoli")

END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
start_dt = "2026-07-22"

t0 = time.time()
data_yf = yf.download(tickers=" ".join(test_tickers), start=start_dt, end=END_FOR_DOWNLOAD,
                       interval="1d", auto_adjust=True, progress=False, threads=True)
elapsed = time.time() - t0
print(f"TEMPO DOWNLOAD: {elapsed:.1f} secondi per {len(test_tickers)} titoli")
print(f"shape: {data_yf.shape}, empty: {data_yf.empty}")
