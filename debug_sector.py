import os, requests, yfinance as yf
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

TODAY = datetime.now().strftime("%Y-%m-%d")
END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

test_tickers = ["AAPL", "MSFT", "DMLP"]
last_dates = {}
for tk in test_tickers:
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":"eq.US","order":"date.desc","limit":"1"})
    row = rp.json()
    last_dates[tk] = row[0]["date"] if row else "2020-01-01"
    print(f"{tk}: ultima data={last_dates[tk]}")

start_dates = list(last_dates.values())
start_dt = min(start_dates)
start_dt = (datetime.strptime(start_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
print(f"\nstart_dt calcolato: {start_dt}")
print(f"end: {END_FOR_DOWNLOAD}")

print("\nScarico da Yahoo...")
data_yf = yf.download(tickers=" ".join(test_tickers), start=start_dt, end=END_FOR_DOWNLOAD,
                       interval="1d", auto_adjust=True, progress=False, threads=True)
print("Scaricato, shape:", data_yf.shape)
print(data_yf.tail(5))

# Prova la scrittura
if not data_yf.empty:
    closes = data_yf["Close"] if len(test_tickers) > 1 else data_yf[["Close"]].rename(columns={"Close": test_tickers[0]})
    price_buf = []
    for tk in test_tickers:
        if tk not in closes.columns:
            print(f"ATTENZIONE: {tk} non trovato nelle colonne scaricate!")
            continue
        for date_idx, price in closes[tk].dropna().items():
            date_str = date_idx.strftime("%Y-%m-%d")
            if date_str > last_dates[tk]:
                price_buf.append({"ticker": tk, "exchange": "US", "date": date_str, "adj_close": round(float(price), 6)})
    print(f"\nRighe nuove da scrivere: {len(price_buf)}")
    print(price_buf[:5])
    if price_buf:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        print(f"Scrittura: HTTP {r.status_code}, testo: {r.text[:300]}")
