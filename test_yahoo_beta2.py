import subprocess
subprocess.run(["pip", "install", "yfinance", "--break-system-packages", "-q"])
import yfinance as yf

for ticker in ["AAPL", "NVDA", "MSFT"]:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        beta = info.get("beta")
        print(f"{ticker}: beta = {beta}")
    except Exception as e:
        print(f"{ticker}: ERRORE {e}")
