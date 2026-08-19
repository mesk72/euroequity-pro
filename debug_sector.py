import os, requests
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi,filtro=None):
    o=[];off=0
    while True:
        p={"select":campi,"limit":"1000","offset":str(off)}
        if filtro: p.update(filtro)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o

print("Carico universo e vista prezzi...")
st=tutte("stocks","ticker,exchange,company,in_universe")
mv=tutte("latest_prices_mv","ticker,exchange")
hanno=set((x["ticker"],x["exchange"]) for x in mv)
print("  stocks: %d | con prezzo: %d" % (len(st),len(hanno)))
print()
print("=== TITOLI IN UNIVERSO SENZA PREZZO (il problema che vedi nella ricerca) ===")
dentro=[x for x in st if x.get("in_universe")]
senza=[x for x in dentro if (x["ticker"],x["exchange"]) not in hanno]
print("  in universo: %d | SENZA PREZZO: %d" % (len(dentro),len(senza)))
per_ex=defaultdict(list)
for x in senza: per_ex[x["exchange"]].append(x)
for ex in sorted(per_ex,key=lambda e:-len(per_ex[e])):
    print("    %-6s %4d" % (ex,len(per_ex[ex])))
    for x in per_ex[ex][:6]:
        print("        %-10s %s" % (x["ticker"],(x.get("company") or "")[:40]))
print()
print("=== TITOLI FUORI UNIVERSO su OM e OB (Svezia/Norvegia) ===")
for ex in ["OM","OB"]:
    fuori=[x for x in st if not x.get("in_universe") and x["exchange"]==ex]
    print("  %-4s fuori universo: %d" % (ex,len(fuori)))
    for x in fuori[:12]:
        print("      %-10s %s" % (x["ticker"],(x.get("company") or "")[:42]))
