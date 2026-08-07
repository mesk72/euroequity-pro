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
def uni(ex):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
def vis(ex):
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
print("%-14s %6s %8s %9s   %s" % ("MERCATO","TOT","AGGIORN","%","dettaglio"))
for nome,lista in G:
    t=sum(uni(e) for e in lista); TOT+=t
    d=[]
    for e in lista: d+=vis(e)
    c=Counter(d)
    top=max(c) if c else "-"
    n=c.get(top,0); AGG+=n
    altri=" | ".join("%s:%d"%(k,v) for k,v in sorted(c.items(),reverse=True)[1:3])
    print("%-14s %6d %8d %8.1f%%   %s %s" % (nome,t,n,n/t*100,top,("| "+altri) if altri else ""))
print()
print("TOTALE: %d aggiornati su %d (%.1f%%)" % (AGG,TOT,AGG/TOT*100))
