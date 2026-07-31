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
        c = df["Close"].dropna()
        ultime = [(i.strftime("%d/%m"), round(float(v),2)) for i,v in list(c.items())[-3:]]
        print("  %-12s ultime chiusure: %s" % (t, ultime))
    except Exception as e:
        print("  %-12s errore: %s" % (t, str(e)[:60]))
