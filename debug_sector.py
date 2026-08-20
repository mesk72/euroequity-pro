import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi,extra=None):
    o=[];off=0
    while True:
        p={"select":campi,"limit":"1000","offset":str(off)}
        if extra: p.update(extra)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
fu=tutte("fundamentals","ticker,exchange,mkt_cap","")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
st=tutte("stocks","ticker,exchange,company,sector,in_universe",{"exchange":"eq.CPSE"})
print("Titoli danesi in anagrafica: %d" % len(st))
print()
righe=[]
for x in st:
    v=mc.get((x["ticker"],"CPSE"))
    righe.append((x["ticker"],(x.get("company") or ""),(x.get("sector") or ""),v,bool(x.get("in_universe"))))
righe.sort(key=lambda z:-(z[3] or 0))
print("=== TUTTI i danesi, ordinati per capitalizzazione ===")
print("%-12s %-40s %-22s %11s %s" % ("TICKER","SOCIETA'","SETTORE","MKT CAP","IN UNIV"))
for tk,az,se,v,u in righe:
    print("%-12s %-40s %-22s %11s %s" % (tk,az[:40],se[:22],
        ("%.1f"%v) if v is not None else "-", "SI" if u else "no"))
print()
esclusi=[r for r in righe if not r[4]]
print("=== ESCLUSI: %d ===" % len(esclusi))
sotto=[r for r in esclusi if r[3] is not None and r[3]<300]
senza=[r for r in esclusi if r[3] is None]
print("  sotto i 300 MM: %d" % len(sotto))
print("  senza capitalizzazione: %d" % len(senza))
