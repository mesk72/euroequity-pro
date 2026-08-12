import os, requests, yfinance as yf, pandas as pd, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== La borsa di Tokyo era APERTA l'11 agosto? ===")
for yt in ["7203.T","6758.T","9984.T","8306.T"]:
    df=yf.download(yt,start="2026-08-06",end="2026-08-13",interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    print("  %-8s sedute: %s" % (yt,[i.strftime("%d/%m") for i in cl.index]))
    time.sleep(0.3)
print()
print("=== I 3 titoli segnalati: Yahoo ha davvero l'11 agosto? ===")
for tk,ex,yt in [("ECT","AS","ECT.AS"),("EIOS","VI","EIOS.VI"),("ICGC","LSE","ICGC.L")]:
    df=yf.download(yt,start="2026-08-06",end="2026-08-13",interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    print("  %-8s %s" % (yt,[(i.strftime("%d/%m"),round(float(v),2)) for i,v in cl.items()]))
    time.sleep(0.3)
