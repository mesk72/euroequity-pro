import yfinance as yf
data = yf.download(tickers="AAPL", start="2026-07-20", end="2026-07-24", interval="1d", auto_adjust=True, progress=False)
print(data)
