import yfinance as yf
from datetime import datetime, timedelta

# Scarico sia Close che Adj Close per GOOGL negli ultimi 7 mesi
data = yf.download(tickers="GOOGL", start="2025-12-01", end="2026-07-29",
                    interval="1d", auto_adjust=False, progress=False)
print("Colonne:", list(data.columns))
print("\nUltimi 3 giorni:")
print(data.tail(3))

# Prezzo di oggi (ultima riga)
last_row = data.iloc[-1]
last_date = data.index[-1]
print(f"\nUltimo giorno: {last_date.date()}, Close={last_row['Close'].values[0] if hasattr(last_row['Close'],'values') else last_row['Close']}")

# Provo diverse definizioni di "6 mesi fa"
today = last_date
candidates = {
    "182 giorni fa": today - timedelta(days=182),
    "6 mesi calendario (stesso giorno)": today.replace(month=today.month-6) if today.month>6 else today.replace(year=today.year-1, month=today.month+6),
    "180 giorni fa": today - timedelta(days=180),
    "26 settimane fa (182gg)": today - timedelta(weeks=26),
}

close_col = data['Close'] if 'GOOGL' not in str(data.columns) else data['Close']['GOOGL'] if hasattr(data['Close'], 'columns') else data['Close']

for label, target in candidates.items():
    target_str = target.strftime("%Y-%m-%d")
    # trovo la riga con data <= target, la piu' vicina
    subset = data[data.index <= target]
    if len(subset) > 0:
        base_date = subset.index[-1]
        base_close = subset['Close'].iloc[-1]
        if hasattr(base_close, 'iloc'):
            base_close = base_close.iloc[0]
        today_close = data['Close'].iloc[-1]
        if hasattr(today_close, 'iloc'):
            today_close = today_close.iloc[0]
        perf = (float(today_close) / float(base_close) - 1) * 100
        print(f"{label} (target {target_str}, usa {base_date.date()}): Close={float(base_close):.2f} -> perf={perf:.2f}%")
