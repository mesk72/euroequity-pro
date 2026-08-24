import os, requests, statistics
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
st=tutte("stocks","ticker,exchange,company,sector,in_universe")
fu=tutte("fundamentals","ticker,exchange,rev_growth,eps_growth,mkt_cap")
f={(x["ticker"],x["exchange"]):x for x in fu}
NA=["US","TSX"]; EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
AP=["TSE","SEHK","ASX","KRX","SGX"]
for area,lista in [("NORD AMERICA",NA),("EUROPA",EU),("ASIA PACIFICO",AP)]:
    print("="*76)
    print("%s" % area)
    print("%-24s %5s %10s %10s %10s   %s" % ("SETTORE","N","PONDERATA","MEDIANA","SCARTO","peggiore anomalia"))
    sett={}
    for x in st:
        if not x.get("in_universe") or x["exchange"] not in lista: continue
        d=f.get((x["ticker"],x["exchange"]))
        if not d or d.get("rev_growth") is None or not d.get("mkt_cap"): continue
        sett.setdefault(x.get("sector") or "(vuoto)",[]).append((x["ticker"],x.get("company") or "",d["rev_growth"],d["mkt_cap"]))
    for s in sorted(sett):
        v=sett[s]
        sw=sum(g*m for _,_,g,m in v); sm=sum(m for _,_,_,m in v)
        pond=sw/sm*100; med=statistics.median([g for _,_,g,_ in v])*100
        worst=max(v,key=lambda z:abs(z[2]))
        flag="  <-- DISTORTO" if abs(pond-med)>15 else ""
        print("%-24s %5d %9.1f%% %9.1f%% %9.1f   %s %.0f%%%s" % (
            s[:24],len(v),pond,med,pond-med,worst[0],worst[2]*100,flag))
    print()
print("="*76)
print("Quanti titoli in tutto hanno una crescita ricavi oltre il 500%%?")
n=sum(1 for x in st if x.get("in_universe") and f.get((x["ticker"],x["exchange"]),{}).get("rev_growth") is not None
      and abs(f[(x["ticker"],x["exchange"])]["rev_growth"])>5)
print("  %d titoli su tutto l'universo" % n)
