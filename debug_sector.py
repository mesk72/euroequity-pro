import os, requests, time
import yfinance as yf, pandas as pd
from collections import Counter
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
GRUPPI=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
        ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),
        ("Hong Kong",["SEHK"]),("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
TUTTI=[e for _,l in GRUPPI for e in l]

def leggi(tab,sel,ex,extra=None):
    out=[];off=0
    while True:
        p={"select":sel,"exchange":"eq."+ex,"limit":"1000","offset":str(off)}
        if extra:p.update(extra)
        try: b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=60).json()
        except Exception: break
        if not isinstance(b,list) or not b: break
        out+=b; off+=1000
        if len(b)<1000: break
    return out

print("=== STATO DOPO L'ALLINEAMENTO ===")
tot=0; c=Counter(); mai=0
righe=[]
for nome,lista in GRUPPI:
    cc=Counter(); mm=0; t=0
    for ex in lista:
        uni={r["ticker"] for r in leggi("stocks","ticker",ex,{"in_universe":"eq.true"})}
        pre={r["ticker"]:r.get("price_date") for r in leggi("latest_prices","ticker,price_date",ex)}
        t+=len(uni)
        for tk in uni:
            d=pre.get(tk)
            if d: cc[d]+=1; c[d]+=1
            else: mm+=1; mai+=1
    tot+=t
    righe.append((nome,t,cc.get("2026-07-31",0),cc.get("2026-07-30",0),
                  sum(v for k,v in cc.items() if k<"2026-07-30"),mm))
print("%-14s %6s %7s %7s %8s %5s" % ("MERCATO","TOT","31/07","30/07","+VECCHI","MAI"))
for r in righe: print("%-14s %6d %7d %7d %8d %5d" % r)
print()
print("TOTALE UNIVERSO: %d" % tot)
for d,n in sorted(c.items(),reverse=True)[:4]:
    print("  %s : %5d titoli (%.1f%%)" % (d,n,n/tot*100))
print("  mai scritti: %d" % mai)

print()
print("=== CONTROLLO TICKER SOSPETTI ===")
prove=[("823","SEHK","Link REIT",["0823.HK","823.HK"]),
       ("778","SEHK","Fortune REIT",["0778.HK","778.HK"]),
       ("ACO.X","TSX","ATCO",["ACO-X.TO","ACO.X.TO"]),
       ("IIP.UN","TSX","InterRent REIT",["IIP-UN.TO","IIP.UN.TO"]),
       ("GO.U","TSX","GO Residential REIT",["GO-U.TO","GO.U.TO"]),
       ("AT.","LSE","Ashtead Technology",["AT.L","ATL.L"]),
       ("ROKO B","OM","Roko AB",["ROKO-B.ST","ROKOB.ST"]),
       ]
for tk,ex,nome,cand in prove:
    print("\n%s (%s.%s)" % (nome,tk,ex))
    for yt in cand:
        try:
            df=yf.download(yt,period="6d",interval="1d",auto_adjust=True,progress=False)
            if df.empty: print("   %-14s vuoto" % yt); continue
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            if len(cl)==0: print("   %-14s vuoto" % yt); continue
            print("   %-14s FUNZIONA -> ultima %s = %.2f" % (yt,cl.index[-1].strftime("%d/%m"),float(cl.iloc[-1])))
        except Exception as e:
            print("   %-14s errore %s" % (yt,str(e)[:40]))
        time.sleep(0.4)
