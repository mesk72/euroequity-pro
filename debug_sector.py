import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
G=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
   ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),("Hong Kong",["SEHK"]),
   ("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
def leggi(tab,sel,ex,extra=None):
    o=[];off=0
    while True:
        p={"select":sel,"exchange":"eq."+ex,"limit":"1000","offset":str(off)}
        if extra:p.update(extra)
        try: b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=60).json()
        except Exception: break
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
print("=== STATO PREZZI (dalla vista latest_prices_mv) ===")
tot=0; agg=0
for nome,lista in G:
    c=Counter()
    for ex in lista:
        for r in leggi("latest_prices_mv","ticker,price_date",ex):
            c[r["price_date"]]+=1
    n=sum(c.values()); tot+=n
    prev=c.most_common(1)[0] if c else ("-",0)
    print("  %-14s %5d titoli  prevalente %s (%d)  altre date: %s" %
          (nome,n,prev[0],prev[1],dict(list(c.most_common())[1:4])))
print("\n  TOTALE nella vista: %d" % tot)
print()
print("=== Esecuzioni EU nelle ultime 18 ore ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_eu_yahoo","order":"created_at.desc","limit":"3"})
for x in r.json():
    print(" ",x["created_at"])
    for riga in x["log_text"].split("\n"):
        if any(k in riga for k in ["Prezzi Yahoo","vista aggiornata","ERRORE","BLOCCO SICUREZZA"]):
            print("     ",riga.strip())
