import yfinance as yf
data = yf.download(tickers="AAPL MSFT NVDA", start="2026-07-20", end="2026-07-27", interval="1d", auto_adjust=True, progress=False, threads=True)
print(data)
print("\nColonne:", data.columns.tolist() if hasattr(data.columns, 'tolist') else data.columns)
