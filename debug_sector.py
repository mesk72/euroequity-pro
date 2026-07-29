import os, requests, yfinance as yf
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

exchanges = ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
all_rows = []
for ex in exchanges:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
            params={"select":"ticker,exchange,price_date","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
        rows = r.json()
        if not isinstance(rows, list) or not rows: break
        all_rows.extend(rows)
        offset += 1000
        if len(rows) < 1000: break

dates = Counter(r["price_date"] for r in all_rows)
top_date = dates.most_common(1)[0][0]
stale = [r for r in all_rows if r["price_date"] != top_date]
print(f"Totale fermi: {len(stale)}, data prevalente={top_date}")

# suffix map Yahoo per exchange
suffix = {"MIL":".MI","XETRA":".DE","PA":".PA","LSE":".L","SWX":".SW","OM":".ST","OB":".OL",
          "CPSE":".CO","AS":".AS","MC":".MC","BR":".BR","LS":".LS","VI":".VI","HE":".HE","IR":".IR","GR":".AT"}

sample = stale[:25]
ytickers = [s["ticker"] + suffix.get(s["exchange"], "") for s in sample]
df = yf.download(ytickers, period="6d", interval="1d", auto_adjust=True, progress=False, group_by="ticker")

confirmed_yahoo_lag = []
real_bug = []
for s, yt in zip(sample, ytickers):
    try:
        import pandas as pd
        close_series = df[yt]["Close"] if isinstance(df.columns, pd.MultiIndex) else df["Close"]
        last_valid = close_series.dropna()
        if len(last_valid) == 0:
            real_bug.append((s["ticker"], s["exchange"], "yahoo vuoto"))
            continue
        last_date_yahoo = last_valid.index[-1].strftime("%Y-%m-%d")
        our_date = s["price_date"]
        if last_date_yahoo <= our_date:
            confirmed_yahoo_lag.append((s["ticker"], s["exchange"], our_date, last_date_yahoo))
        else:
            real_bug.append((s["ticker"], s["exchange"], f"nostro={our_date} ma yahoo ha={last_date_yahoo}"))
    except Exception as e:
        real_bug.append((s["ticker"], s["exchange"], f"errore lettura: {e}"))

print(f"\nConfermato ritardo Yahoo (yahoo non ha piu' di noi): {len(confirmed_yahoo_lag)}/{len(sample)}")
for x in confirmed_yahoo_lag: print(" ", x)
print(f"\nBUG REALE (yahoo ha dati piu' recenti di noi, o yahoo vuoto): {len(real_bug)}/{len(sample)}")
for x in real_bug: print(" ", x)
