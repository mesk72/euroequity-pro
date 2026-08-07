import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

def leggi(tab, sel, ex, extra=None):
    out=[];off=0
    while True:
        p={"select":sel,"exchange":"eq."+ex,"limit":"1000","offset":str(off)}
        if extra: p.update(extra)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=60).json()
        if not isinstance(b,list) or not b: break
        out+=b; off+=1000
        if len(b)<1000: break
    return out

uni=leggi("stocks","ticker,company,yahoo_ticker","US",{"in_universe":"eq.true"})
mv=leggi("latest_prices_mv","ticker,price_date","US")
dmap={x["ticker"]:x["price_date"] for x in mv}
c=Counter(dmap.values())
seduta=max(c) if c else None
print("Universo USA: %d titoli | ultima seduta presente: %s (%d titoli)" % (len(uni),seduta,c.get(seduta,0)))
indietro=[x for x in uni if dmap.get(x["ticker"])!=seduta]
print("NON alla seduta %s: %d titoli" % (seduta,len(indietro)))
print()

nostri=[]; delistati=[]
for x in indietro:
    tk=x["ticker"]; yt=x.get("yahoo_ticker") or tk
    try:
        df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
        if df.empty:
            delistati.append((tk,x.get("company") or "",dmap.get(tk),"Yahoo vuoto")); time.sleep(0.25); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        if len(cl)==0:
            delistati.append((tk,x.get("company") or "",dmap.get(tk),"Yahoo vuoto")); time.sleep(0.25); continue
        date=[i.strftime("%Y-%m-%d") for i in cl.index]
        if seduta in date:
            val=float(cl.iloc[date.index(seduta)])
            nostri.append((tk,x.get("company") or "",dmap.get(tk),val))
        else:
            delistati.append((tk,x.get("company") or "",dmap.get(tk),"ultimo su Yahoo: "+date[-1]))
    except Exception as e:
        delistati.append((tk,x.get("company") or "",dmap.get(tk),"errore"))
    time.sleep(0.25)

print("=== COLPA NOSTRA: Yahoo HA la seduta %s ma noi no (%d) ===" % (seduta,len(nostri)))
for tk,az,nostro,val in nostri:
    print("  %-8s %-38s noi=%s  yahoo=%.2f" % (tk,az[:38],nostro,val))
print()
print("=== NON COLPA NOSTRA: Yahoo non ha la seduta (%d) ===" % len(delistati))
for tk,az,nostro,mot in delistati:
    print("  %-8s %-38s noi=%s  %s" % (tk,az[:38],nostro,mot))
