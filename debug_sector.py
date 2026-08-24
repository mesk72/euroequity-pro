import os, requests
from collections import defaultdict
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
st=tutte("stocks","ticker,exchange,company,sector,in_universe")
fu=tutte("fundamentals","ticker,exchange,rev_growth,eps_growth,mkt_cap")
uni={(x["ticker"],x["exchange"]):x for x in st if x.get("in_universe")}
f={(x["ticker"],x["exchange"]):x for x in fu}
US=[k for k in uni if k[1]=="US"]
hc=[k for k in US if (uni[k].get("sector") or "")=="Health Care"]
print("Titoli Health Care USA in universo: %d" % len(hc))
dati=[(k[0],uni[k].get("company") or "",f.get(k,{}).get("rev_growth"),f.get(k,{}).get("mkt_cap")) for k in hc]
val=[d for d in dati if d[2] is not None and d[3] is not None]
print("con rev_growth e mkt_cap: %d" % len(val))
print()
sw=sum(d[2]*d[3] for d in val); sm=sum(d[3] for d in val)
import statistics
sem=[d[2] for d in val]
print("MEDIA PONDERATA per capitalizzazione: %.1f%%" % (sw/sm*100))
print("MEDIA SEMPLICE:                       %.1f%%" % (sum(sem)/len(sem)*100))
print("MEDIANA:                              %.1f%%" % (statistics.median(sem)*100))
print()
print("=== valori piu' ESTREMI (probabili anomalie) ===")
for t,az,g,mc in sorted(val,key=lambda z:-abs(z[2]))[:15]:
    print("  %-8s %-34s rev_growth=%9.1f%%  mkt_cap=%10.0f" % (t,az[:34],g*100,mc))
print()
print("=== contributo alla media ponderata ===")
for t,az,g,mc in sorted(val,key=lambda z:-abs(z[2]*z[3]))[:10]:
    print("  %-8s %-30s contributo %6.1f punti  (g=%.0f%% mc=%.0f)" % (t,az[:30],g*mc/sm*100,g*100,mc))
