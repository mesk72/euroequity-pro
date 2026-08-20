import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi,extra=None):
    o=[];off=0
    while True:
        p={"select":campi,"limit":"1000","offset":str(off)}
        if extra: p.update(extra)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
st=tutte("stocks","ticker,exchange,in_universe")
fu=tutte("fundamentals","ticker,exchange,value_score,mkt_cap")
mv=tutte("latest_prices_mv","ticker,exchange")
uni=[(x["ticker"],x["exchange"]) for x in st if x.get("in_universe")]
setf=set((x["ticker"],x["exchange"]) for x in fu)
setm=set((x["ticker"],x["exchange"]) for x in mv)
print("universo:            %d" % len(uni))
print("con riga fondamentali: %d   -> SENZA: %d" % (sum(1 for k in uni if k in setf), sum(1 for k in uni if k not in setf)))
print("con prezzo nella vista: %d   -> SENZA: %d" % (sum(1 for k in uni if k in setm), sum(1 for k in uni if k not in setm)))
print()
senza_f=[k for k in uni if k not in setf]
print("=== titoli in universo SENZA fondamentali: %d ===" % len(senza_f))
c=Counter(k[1] for k in senza_f)
for ex,n in c.most_common(): print("   %-6s %4d" % (ex,n))
print()
print("  esempi:", senza_f[:12])
