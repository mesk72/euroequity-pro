import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
SED="2026-08-07"
resti=[]
for ex in EX:
    mv=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"ticker,price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        mv+=b; off+=1000
        if len(b)<1000: break
    for x in mv:
        if x["price_date"]<SED: resti.append((ex,x["ticker"],x["price_date"]))
print("Titoli ancora indietro rispetto al 7/8: %d" % len(resti))
print()
nostri=[];loro=[]
for ex,tk,nostro in resti:
    y=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"yahoo_ticker,company","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    yt=(y[0].get("yahoo_ticker") if y else None) or tk
    az=(y[0].get("company") if y else "") or ""
    try:
        df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        d=[i.strftime("%Y-%m-%d") for i in cl.index]
        if SED in d: nostri.append((tk,ex,az,nostro))
        else: loro.append((tk,ex,az,nostro,d[-1] if d else "nessuna"))
    except Exception:
        loro.append((tk,ex,az,nostro,"errore"))
    time.sleep(0.25)
print("=== ANCORA COLPA NOSTRA (%d) ===" % len(nostri))
for tk,ex,az,n in nostri: print("  %-10s %-6s %-34s noi=%s" % (tk,ex,az[:34],n))
print()
print("=== Yahoo non ce l'ha (%d) ===" % len(loro))
for tk,ex,az,n,u in loro: print("  %-10s %-6s %-34s noi=%s  yahoo si ferma a %s" % (tk,ex,az[:34],n,u))
