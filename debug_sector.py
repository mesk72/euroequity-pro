import yfinance as yf, pandas as pd
from datetime import datetime
print("Ora test (UTC):", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print()
prova = [("ASML.AS","non fra i 383"),("SAP.DE","non fra i 383"),("MC.PA","non fra i 383"),
         ("SHEL.L","non fra i 383"),("ISP.MI","non fra i 383"),
         ("AKTIA.HE","FRA I 383"),("BURE.ST","FRA I 383"),("ALMB.CO","FRA I 383")]
for t, nota in prova:
    try:
        df = yf.download(t, period="6d", interval="1d", auto_adjust=True, progress=False)
        cl = df["Close"]
        if isinstance(cl, pd.DataFrame): cl = cl.iloc[:,0]
        cl = cl.dropna()
        ultime = ["%s=%.2f" % (cl.index[i].strftime("%d/%m"), float(cl.iloc[i]))
                  for i in range(max(0,len(cl)-3), len(cl))]
        ha30 = any(cl.index[i].strftime("%Y-%m-%d")=="2026-07-30" for i in range(len(cl)))
        print("  %-10s %-14s  30/07: %s   %s" % (t, nota, "SI" if ha30 else "NO", "  ".join(ultime)))
    except Exception as e:
        print("  %-10s errore %s" % (t, str(e)[:50]))
