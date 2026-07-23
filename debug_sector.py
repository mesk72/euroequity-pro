import yfinance as yf
print("Test disponibilita' dati Yahoo per AAPL, ultimi 5 giorni:")
data = yf.download(tickers="AAPL", start="2026-07-18", end="2026-07-24", interval="1d", auto_adjust=True, progress=False)
print(data)
print("\nUltima data disponibile:", data.index[-1] if len(data) > 0 else "NESSUN DATO")
