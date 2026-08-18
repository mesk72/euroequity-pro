import os, requests
from collections import Counter, defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

def tutte(tab, campi, filtro=None):
    o=[];off=0
    while True:
        p={"select":campi,"limit":"1000","offset":str(off)}
        if filtro: p.update(filtro)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o

print("Carico stocks e fundamentals...")
st=tutte("stocks","ticker,exchange,company,sector,in_universe,yahoo_ticker")
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
print("  stocks: %d | fundamentals: %d" % (len(st),len(fu)))
print()

dentro=[x for x in st if x.get("in_universe")]
fuori=[x for x in st if not x.get("in_universe")]
print("IN UNIVERSO: %d | FUORI: %d" % (len(dentro),len(fuori)))
print()

print("=== DISTRIBUZIONE della capitalizzazione, DENTRO vs FUORI ===")
def fasce(lista,eti):
    f=Counter()
    for x in lista:
        v=mc.get((x["ticker"],x["exchange"]))
        if v is None: f["assente"]+=1
        elif v<1: f["<1"]+=1
        elif v<10: f["1-10"]+=1
        elif v<100: f["10-100"]+=1
        elif v<500: f["100-500"]+=1
        elif v<5000: f["500-5.000"]+=1
        else: f[">5.000"]+=1
    print("  %s:" % eti)
    for k in ["assente","<1","1-10","10-100","100-500","500-5.000",">5.000"]:
        if f[k]: print("     %-12s %5d" % (k,f[k]))
fasce(dentro,"DENTRO universo")
fasce(fuori,"FUORI universo")
print()
print("Se il campo fosse coerente, i titoli DENTRO dovrebbero stare tutti")
print("sopra la soglia (500 milioni per l'Europa). Vediamo se e' cosi'.")
print()
print("=== titoli DENTRO con capitalizzazione sotto 1 (implausibile) ===")
strani=[(x["ticker"],x["exchange"],(x.get("company") or "")[:30],mc.get((x["ticker"],x["exchange"])))
        for x in dentro if mc.get((x["ticker"],x["exchange"])) is not None and mc[(x["ticker"],x["exchange"])]<1]
print("  quanti:",len(strani))
for t in strani[:15]: print("    %-10s %-5s %-30s %s" % t)
