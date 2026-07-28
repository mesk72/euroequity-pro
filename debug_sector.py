import yfinance as yf
data = yf.download(tickers="SAP.DE", start="2026-07-24", end="2026-07-29", interval="1d", auto_adjust=True, progress=False)
print(data)
