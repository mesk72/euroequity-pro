import os, requests, statistics
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
uni=set(); nomi={}
for ex in EU:
    off=0
    while True:
        b=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,company","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        for x in b:
            uni.add((x["ticker"],ex)); nomi[(x["ticker"],ex)]=x.get("company") or ""
        off+=len(b)
val=[]
for ex in EU:
    off=0
    while True:
        b=requests.get(U+"/rest/v1/fundamentals",headers=H,
            params={"select":"ticker,mkt_cap","exchange":"eq."+ex,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        for x in b:
            if (x["ticker"],ex) in uni and x.get("mkt_cap"): val.append((x["ticker"],ex,x["mkt_cap"]))
        off+=len(b)
val.sort(key=lambda z:-z[2])
print("titoli europei in universo con capitalizzazione: %d" % len(val))
print()
top=val[:500]; m=[v for _,_,v in top]
print("=== PRIMI 500 TITOLI EUROPEI ===")
print("  MEDIANA:  %9.0f milioni = %6.1f miliardi USD" % (statistics.median(m), statistics.median(m)/1000))
print("  MEDIA:    %9.0f milioni = %6.1f miliardi" % (sum(m)/len(m), sum(m)/len(m)/1000))
print("  massimo:  %9.0f milioni = %6.0f mld (%s.%s)" % (top[0][2],top[0][2]/1000,top[0][0],top[0][1]))
print("  minimo:   %9.0f milioni = %6.1f mld (%s.%s)" % (top[-1][2],top[-1][2]/1000,top[-1][0],top[-1][1]))
print("  somma:    %9.0f milioni = %6.2f trilioni" % (sum(m), sum(m)/1e6))
print()
q=statistics.quantiles(m,n=4)
print("  quartili: Q1 %.1f mld | Q2 %.1f mld | Q3 %.1f mld" % (q[0]/1000,q[1]/1000,q[2]/1000))
print()
print("  primi 10 europei:")
for t,ex,v in top[:10]: print("    %-9s %-5s %7.0f mld  %s" % (t,ex,v/1000,nomi.get((t,ex),"")[:30]))
