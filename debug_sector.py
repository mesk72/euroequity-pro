import yfinance as yf, pandas as pd
from datetime import datetime
print("Ora del test (UTC):", datetime.utcnow())
print()
print("Yahoo ha la chiusura di GIOVEDI 30/07 per questi titoli europei?")
for t in ["ASML.AS","SAP.DE","MC.PA","NESN.SW","SHEL.L","ISP.MI","NOKIA.HE","VOLV-B.ST"]:
    try:
        df = yf.download(t, period="6d", interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            print("  %-12s VUOTO" % t); continue
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        ultime = []
        for i in range(max(0, len(close)-3), len(close)):
            ultime.append("%s=%.2f" % (close.index[i].strftime("%d/%m"), float(close.iloc[i])))
        print("  %-12s %s" % (t, "  ".join(ultime)))
    except Exception as e:
        print("  %-12s errore: %s" % (t, str(e)[:70]))
