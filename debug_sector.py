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
def leggi(tab,ex,campo):
    out=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/"+tab,headers=H,
            params={"select":campo,"exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        out+=[x[campo] for x in b]; off+=1000
        if len(b)<1000: break
    return out
TOT=0; AGG=0
print()
print("%-14s %6s %8s %7s   %s" % ("MERCATO","TOT","AGGIORN","MANCA","ultima seduta"))
for nome,lista in G:
    t=sum(uni(e) for e in lista); TOT+=t
    d=[]
    for e in lista: d+=leggi("latest_prices_mv",e,"price_date")
    c=Counter(d); top=max(c) if c else "-"
    n=c.get(top,0); AGG+=n
    print("%-14s %6d %8d %7d   %s" % (nome,t,n,t-n,top))
print()
print("TOTALE: %d titoli | aggiornati all'ultima seduta del loro mercato: %d (%.1f%%) | mancano %d"
      % (TOT,AGG,AGG/TOT*100,TOT-AGG))
print()
print("=== cosa dicono i log della fase nuova ===")
for nome in ["daily_eu_yahoo","daily_us_yahoo","daily_apac_yahoo"]:
    r=requests.get(U+"/rest/v1/script_logs",headers=H,
        params={"select":"created_at,log_text","script_name":"eq."+nome,"order":"created_at.desc","limit":"1"}).json()
    if not r: continue
    print("--- %s (%s) ---" % (nome,r[0]["created_at"][:19]))
    for riga in r[0]["log_text"].split("\n"):
        if any(k in riga for k in ["RISULTATO","ATTENZIONE","non disponibili su Yahoo","da verificare singolarmente"]):
            print("   ",riga.strip()[:125])
