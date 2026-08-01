import os, requests, time
import yfinance as yf, pandas as pd
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

# (ticker interno, exchange, ticker Yahoo corretto, ora limite UTC del mercato)
FIX=[("823","SEHK","0823.HK",10),
     ("778","SEHK","0778.HK",10),
     ("ACO.X","TSX","ACO-X.TO",22),
     ("GO.U","TSX","GO-U.TO",22),
     ("AT.","LSE","AT.L",17),
     ("ROKO B","OM","ROKO-B.ST",17)]

def conclusa(ds,limite):
    try: d=datetime.strptime(ds,"%Y-%m-%d")
    except Exception: return False
    return datetime.utcnow()>=d.replace(hour=limite,minute=0,second=0)

print("=== 1. Correggo yahoo_ticker ===")
for tk,ex,yt,_ in FIX:
    r=requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+tk,"exchange":"eq."+ex},json={"yahoo_ticker":yt})
    print("  %-9s %-5s -> %-12s HTTP %s" % (tk,ex,yt,r.status_code))

print("\n=== 2. Scarico 5 anni di storico ===")
inizio=(datetime.utcnow()-timedelta(days=5*365+10)).strftime("%Y-%m-%d")
fine=(datetime.utcnow()+timedelta(days=2)).strftime("%Y-%m-%d")
for tk,ex,yt,lim in FIX:
    try:
        df=yf.download(yt,start=inizio,end=fine,interval="1d",auto_adjust=True,progress=False)
        if df.empty: print("  %-9s VUOTO" % tk); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        righe={}
        saltate=0
        for idx,val in cl.items():
            ds=idx.strftime("%Y-%m-%d")
            if not conclusa(ds,lim): saltate+=1; continue
            righe[ds]={"ticker":tk,"exchange":ex,"date":ds,"adj_close":round(float(val),6)}
        righe=list(righe.values())
        scritte=0
        for i in range(0,len(righe),500):
            rw=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=righe[i:i+500])
            if rw.status_code in (200,201,204): scritte+=len(righe[i:i+500])
            else: print("     ERRORE %s: %s" % (rw.status_code,rw.text[:120]))
        print("  %-9s %5d righe (%s -> %s)%s" % (tk,scritte,
            righe[0]["date"] if righe else "-", righe[-1]["date"] if righe else "-",
            "  [%d saltate: seduta aperta]"%saltate if saltate else ""))
    except Exception as e:
        print("  %-9s ERRORE %s" % (tk,str(e)[:60]))
    time.sleep(1)

print("\n=== 3. Aggiorno cache ===")
batch=[]
for tk,ex,_,_ in FIX:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"2"})
    rows=r.json()
    if not isinstance(rows,list) or not rows: continue
    u=rows[0]; p=rows[1] if len(rows)>1 else None
    chg=round(u["adj_close"]/p["adj_close"]-1,6) if (p and p.get("adj_close")) else None
    pp=(u["adj_close"]/(1+chg)) if (chg is not None and (1+chg)!=0) else None
    batch.append({"ticker":tk,"exchange":ex,"price":u["adj_close"],"prev_price":pp,
                  "price_date":u["date"],"change1d":chg})
rw=requests.post(U+"/rest/v1/latest_prices?on_conflict=ticker,exchange",headers=HU,json=batch)
print("  aggiornati %d titoli (HTTP %s)" % (len(batch),rw.status_code))

print("\n=== 4. VERIFICA ===")
for tk,ex,_,_ in FIX:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"limit":"1"})
    n=rc.headers.get("content-range","0/0").split("/")[-1]
    b=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"price_date,price","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("  %-9s %-5s storico:%5s righe   cache: %s" % (tk,ex,n,
        (b[0]["price_date"],b[0]["price"]) if b else "ASSENTE"))
