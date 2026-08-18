import os, requests, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def ripristina(tk,ex,yt,ora_lim=17):
    requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+tk,"exchange":"eq."+ex},json={"in_universe":True})
    inizio=(datetime.utcnow()-timedelta(days=5*365+10)).strftime("%Y-%m-%d")
    df=yf.download(yt,start=inizio,end=(datetime.utcnow()+timedelta(days=1)).strftime("%Y-%m-%d"),
                   interval="1d",auto_adjust=True,progress=False)
    if df.empty: return 0
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    r={}
    for i,v in cl.items():
        ds=i.strftime("%Y-%m-%d")
        if datetime.utcnow() < datetime.strptime(ds,"%Y-%m-%d").replace(hour=ora_lim): continue
        r[ds]={"ticker":tk,"exchange":ex,"date":ds,"adj_close":round(float(v),6)}
    r=list(r.values()); ok=0
    for i in range(0,len(r),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=r[i:i+500])
        if w.status_code in (200,201,204): ok+=len(r[i:i+500])
    return ok

for tk,ex,yt in [("NEOBO","OM","NEOBO.ST"),("NIVI B","OM","NIVI-B.ST")]:
    n=ripristina(tk,ex,yt)
    print("%-8s %-4s -> %d righe di storico" % (tk,ex,n))

print()
print("=== QUANTI ALTRI hanno mkt_cap sospettosamente piccola ed e' per questo che sono fuori? ===")
esc=[];off=0
while True:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,yahoo_ticker,sector","in_universe":"eq.false","limit":"1000","offset":str(off)})
    b=r.json()
    if not isinstance(b,list) or not b: break
    esc+=b; off+=1000
    if len(b)<1000: break
print("  esclusi totali:", len(esc))
# quanti hanno fondamentali con mkt_cap < 10 (cioe' sotto 10 milioni: implausibile per societa' quotate vere)
sospetti=[]
for x in esc:
    if not x.get("yahoo_ticker"): continue
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"mkt_cap,value_score","ticker":"eq."+x["ticker"],"exchange":"eq."+x["exchange"]}).json()
    if f and f[0].get("mkt_cap") is not None and f[0]["mkt_cap"] < 10:
        sospetti.append((x["ticker"],x["exchange"],(x.get("company") or "")[:32],f[0]["mkt_cap"]))
    if len(sospetti)>=40: break
print("  con capitalizzazione sotto 10 (implausibile) - primi %d:" % len(sospetti))
for t in sospetti[:40]: print("    %-10s %-5s %-32s mkt_cap=%s" % t)
