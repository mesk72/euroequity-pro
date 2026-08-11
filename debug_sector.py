import os, requests
from collections import Counter
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
G=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
   ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),("Hong Kong",["SEHK"]),
   ("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
print("Ora UTC:", datetime.utcnow().strftime("%H:%M"))
print("%-14s %6s  %s" % ("MERCATO","TOT","distribuzione"))
TOT=0;AGG=0
for nome,lista in G:
    d=[]
    t=0
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
    c=Counter(d); top=max(c) if c else "-"
    TOT+=t; AGG+=c.get(top,0)
    print("%-14s %6d  %s : %d" % (nome,t,top,c.get(top,0)))
print()
print("TOTALE %d | all'ultima seduta: %d (%.1f%%)" % (TOT,AGG,AGG/TOT*100))
