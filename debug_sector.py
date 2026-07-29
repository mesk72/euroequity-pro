import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

data = yf.download(tickers="GOOGL", start="2025-06-01", end="2026-07-29",
                    interval="1d", auto_adjust=False, progress=False)

today = data.index[-1]
today_close = float(data['Close'].iloc[-1].iloc[0] if hasattr(data['Close'].iloc[-1],'iloc') else data['Close'].iloc[-1])
print(f"Oggi: {today.date()}, Close={today_close:.2f}\n")

periods = {
    "1 settimana": relativedelta(weeks=1),
    "1 mese": relativedelta(months=1),
    "6 mesi": relativedelta(months=6),
    "12 mesi": relativedelta(months=12),
}

for label, delta in periods.items():
    target = today - delta
    subset = data[data.index <= target]
    if len(subset) > 0:
        base_date = subset.index[-1]
        base_close = subset['Close'].iloc[-1]
        if hasattr(base_close, 'iloc'):
            base_close = base_close.iloc[0]
        base_close = float(base_close)
        perf = (today_close / base_close - 1) * 100
        print(f"{label}: target={target.date()}, usa {base_date.date()} (Close={base_close:.2f}) -> perf={perf:.2f}%")
