import os, requests
from collections import Counter, defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
print("fundamentals:",len(fu))
print()
print("=== per exchange: quanti hanno mkt_cap < 1 (sospetto miliardi) ===")
tot=defaultdict(int); pic=defaultdict(int); mediana=defaultdict(list)
for x in fu:
    ex=x["exchange"]; v=x.get("mkt_cap")
    tot[ex]+=1
    if v is not None:
        mediana[ex].append(v)
        if v<1: pic[ex]+=1
print("%-7s %6s %8s %10s  %s" % ("EX","TOT","<1","% <1","MEDIANA"))
for ex in sorted(tot, key=lambda e:-pic[e]):
    m=sorted(mediana[ex])
    med=m[len(m)//2] if m else 0
    print("%-7s %6d %8d %9.1f%%  %12.2f" % (ex,tot[ex],pic[ex],pic[ex]/tot[ex]*100,med))
