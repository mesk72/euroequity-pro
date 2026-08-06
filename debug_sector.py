import os, requests
from collections import Counter
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
GRUPPI=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
        ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),
        ("Hong Kong",["SEHK"]),("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
def cnt(ex):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
def date_di(ex):
    out=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"ticker,price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        out+=b; off+=1000
        if len(b)<1000: break
    return out

TOT=0; A5=0; A4=0; VECCHI=0; MANCA=0
print()
print("%-14s %6s %8s %8s %8s %7s" % ("MERCATO","TOT","al 05/08","al 04/08","+vecchi","assenti"))
dettaglio={}
for nome,lista in GRUPPI:
    t=sum(cnt(e) for e in lista)
    righe=[]
    for e in lista: righe+=date_di(e)
    c=Counter(x["price_date"] for x in righe)
    a5=c.get("2026-08-05",0); a4=c.get("2026-08-04",0)
    vecchi=sum(v for k,v in c.items() if k<"2026-08-04")
    manca=t-len(righe)
    TOT+=t; A5+=a5; A4+=a4; VECCHI+=vecchi; MANCA+=manca
    dettaglio[nome]=(lista,a4)
    print("%-14s %6d %8d %8d %8d %7d" % (nome,t,a5,a4,vecchi,manca))
print()
print("TOTALE %d titoli: al 05/08 = %d (%.1f%%) | al 04/08 = %d | piu' vecchi = %d | assenti = %d"
      % (TOT,A5,A5/TOT*100,A4,VECCHI,MANCA))
