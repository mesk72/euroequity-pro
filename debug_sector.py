import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def leggi(ex):
    out=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        out+=[x["price_date"] for x in b]
        off+=len(b)
    return out
G=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
   ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),("Hong Kong",["SEHK"]),
   ("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
TOT=0;ALL=0
print("%-14s %6s %10s %8s" % ("MERCATO","TOT","ALLINEATI","%"))
for nome,lista in G:
    t=0;d=[]
    for ex in lista:
        r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
            params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
        t+=int(r.headers.get("content-range","0/0").split("/")[-1])
        d+=leggi(ex)
    c=Counter(d); sed=c.most_common(1)[0][0] if c else "-"
    a=sum(1 for x in d if x>=sed)
    TOT+=t; ALL+=a
    print("%-14s %6d %10d %7.1f%%" % (nome,t,a,a/t*100 if t else 0))
print()
print("TOTALE %d | allineati %d (%.1f%%)" % (TOT,ALL,ALL/TOT*100))
