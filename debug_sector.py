import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

print("1) rimetto NSKOG in universo")
r=requests.patch(U+"/rest/v1/stocks",headers=HP,
    params={"ticker":"eq.NSKOG","exchange":"eq.OB"},json={"in_universe":True})
print("   HTTP",r.status_code)

print("2) scarico 5 anni di storico")
inizio=(datetime.utcnow()-timedelta(days=5*365+10)).strftime("%Y-%m-%d")
df=yf.download("NSKOG.OL",start=inizio,end=(datetime.utcnow()+timedelta(days=1)).strftime("%Y-%m-%d"),
               interval="1d",auto_adjust=True,progress=False)
cl=df["Close"]
if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
cl=cl.dropna()
# blocco sicurezza: niente sedute non ancora chiuse (Oslo chiude 15:30 UTC)
limite=datetime.utcnow()
righe={}
saltate=0
for i,v in cl.items():
    ds=i.strftime("%Y-%m-%d")
    d0=datetime.strptime(ds,"%Y-%m-%d")
    if limite < d0.replace(hour=17): saltate+=1; continue
    righe[ds]={"ticker":"NSKOG","exchange":"OB","date":ds,"adj_close":round(float(v),6)}
righe=list(righe.values())
ok=0
for i in range(0,len(righe),500):
    w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=righe[i:i+500])
    if w.status_code in (200,201,204): ok+=len(righe[i:i+500])
print("   scritte %d righe (%s -> %s), saltate %d (seduta aperta)" % (ok,
    righe[0]["date"] if righe else "-", righe[-1]["date"] if righe else "-", saltate))

print("3) verifica")
rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
    params={"select":"date","ticker":"eq.NSKOG","exchange":"eq.OB","limit":"1"})
print("   righe storico:", rc.headers.get("content-range","?").split("/")[-1])
u=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,adj_close","ticker":"eq.NSKOG","exchange":"eq.OB","order":"date.desc","limit":"2"}).json()
print("   ultime:",u)

print()
print("4) ALTRI titoli esclusi che Yahoo ha ancora: quanti sono?")
esc=[];off=0
while True:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,yahoo_ticker","in_universe":"eq.false","limit":"1000","offset":str(off)})
    b=r.json()
    if not isinstance(b,list) or not b: break
    esc+=b; off+=1000
    if len(b)<1000: break
print("   titoli fuori universo in totale:", len(esc))
con_codice=[x for x in esc if x.get("yahoo_ticker")]
print("   di cui con un codice Yahoo impostato:", len(con_codice))
