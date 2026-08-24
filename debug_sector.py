import os, requests, statistics
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== A) cosa dice la tabella precalcolata per Healthcare ===")
r=requests.get(U+"/rest/v1/sector_quintile_partials",headers=H,
    params={"select":"*","sector":"eq.Healthcare"}).json()
NA=["US","TSX"]; EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
AP=["TSE","SEHK","ASX","KRX","SGX"]
for nome,lista in [("Nord America",NA),("Europa",EU),("Asia Pacifico",AP)]:
    sw=sum(x["sum_rev_weighted"] for x in r if x["exchange"] in lista)
    sm=sum(x["sum_rev_weight"] for x in r if x["exchange"] in lista)
    n=sum(x["n_stocks"] for x in r if x["exchange"] in lista)
    print("  %-14s rev growth = %7.1f%%   (%d titoli)" % (nome, sw/sm*100 if sm else 0, n))
print()
print("=== B) ricalcolo dai dati grezzi, Nord America ===")
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
fu=tutte("fundamentals","ticker,exchange,rev_growth,mkt_cap")
f={(x["ticker"],x["exchange"]):x for x in fu}
hc=[x for x in st if x.get("in_universe") and x.get("sector")=="Healthcare" and x["exchange"] in NA]
val=[]
for x in hc:
    d=f.get((x["ticker"],x["exchange"]))
    if d and d.get("rev_growth") is not None and d.get("mkt_cap"):
        val.append((x["ticker"],x.get("company") or "",d["rev_growth"],d["mkt_cap"]))
print("  titoli: %d | con dati: %d" % (len(hc),len(val)))
sw=sum(g*m for _,_,g,m in val); sm=sum(m for _,_,_,m in val)
sem=[g for _,_,g,_ in val]
print("  ponderata: %7.1f%%" % (sw/sm*100))
print("  semplice:  %7.1f%%" % (sum(sem)/len(sem)*100))
print("  mediana:   %7.1f%%" % (statistics.median(sem)*100))
print()
print("  === valori estremi ===")
for t,az,g,m in sorted(val,key=lambda z:-abs(z[2]))[:12]:
    print("    %-8s %-32s %10.1f%%  mc=%9.0f" % (t,az[:32],g*100,m))
print()
print("  === chi pesa di piu' sulla media ponderata ===")
for t,az,g,m in sorted(val,key=lambda z:-abs(z[2]*z[3]))[:8]:
    print("    %-8s %-28s contributo %6.1f punti (g=%.0f%%)" % (t,az[:28],g*m/sm*100,g*100))
