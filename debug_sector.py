import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
limite=(datetime.utcnow()-timedelta(days=7)).strftime("%Y-%m-%d")

sospetti=[]
for ex in EX:
    uni={}; off=0
    while True:
        r=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,company,yahoo_ticker","in_universe":"eq.true",
                    "exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        for x in b: uni[x["ticker"]]=(x.get("company") or "", x.get("yahoo_ticker") or "")
        off+=1000
        if len(b)<1000: break
    lp={}; off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices",headers=H,
            params={"select":"ticker,price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        for x in b: lp[x["ticker"]]=x.get("price_date")
        off+=1000
        if len(b)<1000: break
    for tk,(comp,yt) in uni.items():
        d=lp.get(tk)
        if d is None:
            sospetti.append((tk,ex,comp,yt,"MAI SCRITTO"))
        elif d < limite:
            sospetti.append((tk,ex,comp,yt,d))

print("Titoli in universo mai scritti o fermi da oltre 7 giorni: %d\n" % len(sospetti))

delistati=[]; vivi=[]; incerti=[]
for tk,ex,comp,yt,stato in sospetti[:70]:
    if not yt:
        incerti.append((tk,ex,comp,stato,"nessun codice Yahoo salvato")); continue
    try:
        df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
        if df.empty:
            delistati.append((tk,ex,comp,stato,"Yahoo non ha dati"))
        else:
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            if len(cl)==0:
                delistati.append((tk,ex,comp,stato,"Yahoo vuoto"))
            else:
                ultima=cl.index[-1].strftime("%Y-%m-%d")
                if ultima>=limite: vivi.append((tk,ex,comp,stato,"Yahoo ha "+ultima))
                else: delistati.append((tk,ex,comp,stato,"Yahoo fermo a "+ultima))
    except Exception as e:
        incerti.append((tk,ex,comp,stato,str(e)[:40]))

print("=== DA TOGLIERE DALL'UNIVERSO (%d) - Yahoo non ha piu' dati recenti ===" % len(delistati))
for tk,ex,comp,stato,nota in delistati:
    print("  %-9s %-5s %-32s nostro:%-12s %s" % (tk,ex,comp[:32],stato,nota))
print("\n=== PROBLEMA NOSTRO (%d) - Yahoo HA i dati ma noi no ===" % len(vivi))
for tk,ex,comp,stato,nota in vivi:
    print("  %-9s %-5s %-32s nostro:%-12s %s" % (tk,ex,comp[:32],stato,nota))
print("\n=== DA GUARDARE A MANO (%d) ===" % len(incerti))
for tk,ex,comp,stato,nota in incerti:
    print("  %-9s %-5s %-32s nostro:%-12s %s" % (tk,ex,comp[:32],stato,nota))
