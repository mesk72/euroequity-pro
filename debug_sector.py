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
print()
print("%-14s %6s %10s %9s %6s  %s" % ("MERCATO","TOT","ALLINEATI","INDIETRO","%","ULTIMA SEDUTA"))
TOT=0; ALL=0
for nome,lista in G:
    t=0; d=[]
    for ex in lista:
        rc=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
            params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
        t+=int(rc.headers.get("content-range","0/0").split("/")[-1])
        off=0
        while True:
            r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
                params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
            b=r.json()
            if not isinstance(b,list) or not b: break
            d+=[x["price_date"] for x in b]; off+=1000
            if len(b)<1000: break
    c=Counter(d); sed=c.most_common(1)[0][0] if c else "-"
    a=sum(1 for x in d if x>=sed)
    TOT+=t; ALL+=a
    print("%-14s %6d %10d %9d %5.1f%%  %s" % (nome,t,a,t-a,a/t*100 if t else 0,sed))
print()
print("TOTALE %d | allineati %d (%.1f%%)" % (TOT,ALL,ALL/TOT*100))
print()
print("=== esecuzioni ultime 12 ore ===")
r=requests.get(U+"/rest/v1/daily_log",headers=H,
    params={"select":"market,created_at,prices_updated","order":"created_at.desc","limit":"8"}).json()
for x in r: print("  %-6s %s" % (x["market"],x["created_at"][:19]))
