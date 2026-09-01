import os, requests, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
DA=(datetime.utcnow()-timedelta(days=45)).strftime("%Y-%m-%d")
print("Cerco scalini oltre il 25%% dal %s in poi..." % DA)
sospetti=[]
for ex in EX:
    righe=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/prices_eod",headers=H,
            params={"select":"ticker,date,adj_close","exchange":"eq."+ex,"date":"gte."+DA,
                    "order":"ticker.asc,date.asc","limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        righe+=b; off+=len(b)
        if off>200000: break
    serie={}
    for r in righe: serie.setdefault(r["ticker"],[]).append((r["date"],r["adj_close"]))
    for tk,s in serie.items():
        for i in range(1,len(s)):
            a,b2=s[i-1][1],s[i][1]
            if a and a>0 and b2 and abs(b2/a-1)>0.25:
                sospetti.append((tk,ex,s[i][0],(b2/a-1)*100)); break
print("titoli con scalino sospetto: %d" % len(sospetti))
for t in sospetti[:25]: print("   %-10s %-5s il %s  %+.0f%%" % t)
print()
inizio=(datetime.utcnow()-timedelta(days=365*5+10)).strftime("%Y-%m-%d")
fine=(datetime.utcnow()+timedelta(days=1)).strftime("%Y-%m-%d")
rif=0
for tk,ex,quando,var in sospetti:
    y=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"yahoo_ticker","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    yt=(y[0].get("yahoo_ticker") if y else None) or tk
    try:
        df=yf.download(yt,start=inizio,end=fine,interval="1d",auto_adjust=True,progress=False)
        if df.empty: continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        r={}
        for i,v in cl.items():
            ds=i.strftime("%Y-%m-%d")
            if ds>=datetime.utcnow().strftime("%Y-%m-%d"): continue
            r[ds]={"ticker":tk,"exchange":ex,"date":ds,"adj_close":round(float(v),6)}
        r=list(r.values()); ok=0
        for i in range(0,len(r),500):
            w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=r[i:i+500])
            if w.status_code in (200,201,204): ok+=len(r[i:i+500])
        rif+=1
        print("   %-10s %-5s -> riscritte %4d sedute" % (tk,ex,ok))
    except Exception as e:
        print("   %-10s %-5s errore %s" % (tk,ex,str(e)[:50]))
    time.sleep(0.5)
print("\nStorico ricostruito per %d titoli" % rif)
