import os, requests
from collections import Counter
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
G=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
   ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),("Hong Kong",["SEHK"]),
   ("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
def univ(ex):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
def vista(ex):
    out=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        out+=[x["price_date"] for x in b]; off+=1000
        if len(b)<1000: break
    return out
TOT=0; AGG=0
print()
print("%-14s %6s %8s %6s   %s" % ("MERCATO","TOT","ULTIMA","AGGIOR","indietro"))
for nome,lista in G:
    t=sum(univ(e) for e in lista); TOT+=t
    d=[]
    for e in lista: d+=vista(e)
    c=Counter(d)
    if not c: print("%-14s %6d   nessun dato" % (nome,t)); continue
    ult=max(c); n=c[ult]; AGG+=n
    altri=sorted([(k,v) for k,v in c.items() if k!=ult],reverse=True)[:2]
    print("%-14s %6d %8s %6d   %s" % (nome,t,ult,n," | ".join("%s:%d"%(k,v) for k,v in altri) or "-"))
print()
print("TOTALE: %d titoli | alla loro ultima seduta: %d (%.1f%%) | indietro: %d"
      % (TOT,AGG,AGG/TOT*100,TOT-AGG))
