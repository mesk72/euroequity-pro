import os, requests, statistics
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
# tutti i titoli USA in universo con capitalizzazione
uni=set();off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    uni.update(x["ticker"] for x in b); off+=len(b)
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,mkt_cap","exchange":"eq.US","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=len(b)
val=[(x["ticker"],x["mkt_cap"]) for x in fu if x["ticker"] in uni and x.get("mkt_cap")]
val.sort(key=lambda z:-z[1])
print("titoli USA in universo con capitalizzazione: %d" % len(val))
print()
top=val[:500]
m=[v for _,v in top]
print("=== PRIMI 500 TITOLI STATUNITENSI ===")
print("  MEDIANA:   %10.0f milioni  = %6.1f miliardi USD" % (statistics.median(m), statistics.median(m)/1000))
print("  MEDIA:     %10.0f milioni  = %6.1f miliardi" % (sum(m)/len(m), sum(m)/len(m)/1000))
print("  massimo:   %10.0f milioni  = %6.0f miliardi (%s)" % (top[0][1],top[0][1]/1000,top[0][0]))
print("  minimo:    %10.0f milioni  = %6.1f miliardi (%s)" % (top[-1][1],top[-1][1]/1000,top[-1][0]))
print("  somma:     %10.0f milioni  = %6.2f trilioni" % (sum(m), sum(m)/1e6))
print()
print("  quartili:")
q=statistics.quantiles(m,n=4)
for i,v in enumerate(q,1): print("    Q%d: %10.0f milioni = %.1f mld" % (i,v,v/1000))
print()
print("  primi 10:")
for t,v in top[:10]: print("    %-7s %8.0f mld" % (t,v/1000))
