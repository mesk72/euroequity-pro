import yfinance as yf
data = yf.download(tickers="7203.T 9984.T 0700.HK", start="2026-07-18", end="2026-07-28", interval="1d", auto_adjust=True, progress=False, threads=True)
print(data)
