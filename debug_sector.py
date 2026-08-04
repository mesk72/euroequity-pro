import yfinance as yf, pandas as pd, os, requests, time
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
# prendo 150 ticker veri del mercato MIL (fermo al 31/7)
r=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.MIL","in_universe":"eq.true","limit":"150"})
rows=r.json()
yts=[(x.get("yahoo_ticker") or (x["ticker"]+".MI")) for x in rows]
print("Test su %d ticker MIL. Cerco chi ha la barra del 2026-08-03." % len(yts))
print("Ora UTC:", datetime.utcnow().strftime("%H:%M"))
print()

def quanti_hanno_il_3(lista, etichetta, **kw):
    t0=time.time()
    df=yf.download(tickers=" ".join(lista),start="2026-07-25",end="2026-08-06",
                   interval="1d",auto_adjust=True,progress=False,**kw)
    if df.empty:
        print("  %-34s VUOTO" % etichetta); return
    cl=df["Close"] if isinstance(df.columns,pd.MultiIndex) else df[["Close"]]
    n=0; tot=0
    for c in cl.columns:
        s=cl[c].dropna()
        date=[i.strftime("%Y-%m-%d") for i in s.index]
        tot+=1
        if "2026-08-03" in date: n+=1
    print("  %-34s %3d/%3d hanno il 3/8   (%.0fs)" % (etichetta,n,tot,time.time()-t0))

quanti_hanno_il_3(yts,"blocco da 150 (come lo script)",threads=True)
time.sleep(3)
quanti_hanno_il_3(yts[:50],"blocco da 50",threads=True)
time.sleep(3)
quanti_hanno_il_3(yts[:20],"blocco da 20",threads=True)
time.sleep(3)
quanti_hanno_il_3(yts[:20],"blocco da 20 SENZA threads",threads=False)
time.sleep(3)
# singoli
n=0
for yt in yts[:8]:
    try:
        d=yf.download(yt,start="2026-07-25",end="2026-08-06",interval="1d",auto_adjust=True,progress=False)
        cl=d["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        if "2026-08-03" in [i.strftime("%Y-%m-%d") for i in cl.dropna().index]: n+=1
    except Exception: pass
    time.sleep(0.4)
print("  %-34s %3d/  8 hanno il 3/8" % ("singoli",n))
