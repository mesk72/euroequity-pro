import yfinance as yf, pandas as pd, time
print("InterRent REIT - provo tutte le varianti plausibili")
cand=["IIP-UN.TO","IIPZF","IIP.TO","IIPUN.TO","IIP-U.TO","IIP-UN.V"]
for yt in cand:
    try:
        df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
        if df.empty: print("  %-12s vuoto" % yt); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        if len(cl)==0: print("  %-12s vuoto" % yt); continue
        print("  %-12s FUNZIONA -> ultima %s = %.2f" % (yt,cl.index[-1].strftime("%d/%m/%Y"),float(cl.iloc[-1])))
    except Exception as e:
        print("  %-12s errore %s" % (yt,str(e)[:45]))
    time.sleep(0.4)

print("\nStorico lungo su IIP-UN.TO (esisteva in passato?)")
try:
    df=yf.download("IIP-UN.TO",start="2024-01-01",end="2026-08-02",interval="1d",auto_adjust=True,progress=False)
    if df.empty: print("  nessun dato dal 2024")
    else:
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        print("  righe: %d   dal %s al %s   ultimo prezzo %.2f" % (
            len(cl),cl.index[0].strftime("%d/%m/%Y"),cl.index[-1].strftime("%d/%m/%Y"),float(cl.iloc[-1])))
except Exception as e:
    print("  errore:",str(e)[:60])
