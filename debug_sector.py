import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

stuck = ['4974','6961','6976','6995','7003','7014','7148','7157','7167','7172',
         '7177','7261','7322','7327','7380','7384','7456','8098','8129','8133',
         '8153','8179','8214','8267','8283','8345','7734','7806','8346','7832']

# Scarica in BULK, come fa lo script vero (chunk unico via yfinance multi-ticker)
ytickers = [t.lstrip("0") + ".T" for t in stuck]
df = yf.download(ytickers, period="5d", interval="1d", auto_adjust=True, progress=False, group_by="ticker")

has_jul29 = []
missing_jul29 = []
for t, yt in zip(stuck, ytickers):
    try:
        close_series = df[yt]["Close"] if isinstance(df.columns, __import__('pandas').MultiIndex) else df["Close"]
        last_valid = close_series.dropna()
        if len(last_valid) == 0:
            missing_jul29.append((t, "nessun dato in 5gg"))
            continue
        last_date = last_valid.index[-1].strftime("%Y-%m-%d")
        if last_date >= "2026-07-29":
            has_jul29.append((t, last_date, float(last_valid.iloc[-1])))
        else:
            missing_jul29.append((t, f"ultimo disponibile: {last_date}"))
    except Exception as e:
        missing_jul29.append((t, f"errore: {e}"))

print(f"Con dato 29/7 disponibile su YAHOO ma NON nel nostro DB: {len(has_jul29)}")
for x in has_jul29: print(" ", x)
print(f"\nSenza dato 29/7 nemmeno su Yahoo (genuino ritardo Yahoo): {len(missing_jul29)}")
for x in missing_jul29: print(" ", x)
