import os, requests, yfinance as yf
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica la lista ASX nello stesso ordine dello script reale
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

CHUNK = 150
for i in range(0, len(tickers), CHUNK):
    chunk = tickers[i:i+CHUNK]
    if "BHP" in chunk:
        print(f"BHP e' nel chunk bulk #{i//CHUNK}, posizione {chunk.index('BHP')} su {len(chunk)} titoli")
        ytickers = [t + ".AX" for t in chunk]
        data_yf = yf.download(ytickers, start="2026-07-20", end="2026-07-30",
                               interval="1d", auto_adjust=True, progress=False, group_by="column")
        print("Colonne livello 0:", list(data_yf.columns.levels[0])[:5] if hasattr(data_yf.columns, 'levels') else "N/A")
        if isinstance(data_yf.columns, type(data_yf.columns)) and hasattr(data_yf.columns, 'get_level_values'):
            if "Close" in data_yf.columns.get_level_values(0):
                closes = data_yf.xs("Close", axis=1, level=0)
            else:
                closes = data_yf.xs("Close", axis=1, level=1)
        print("\nBHP.AX in colonne:", "BHP.AX" in closes.columns)
        if "BHP.AX" in closes.columns:
            print("\nDati BHP.AX nel download BULK (chunk 150 titoli):")
            print(closes["BHP.AX"])
        break
