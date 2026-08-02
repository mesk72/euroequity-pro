import os, requests
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]

def leggi(tab,sel,ex,extra=None):
    out=[];off=0
    while True:
        p={"select":sel,"exchange":"eq."+ex,"limit":"1000","offset":str(off)}
        if extra:p.update(extra)
        try: b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=60).json()
        except Exception: break
        if not isinstance(b,list) or not b: break
        out+=b; off+=1000
        if len(b)<1000: break
    return out

# settore per ogni titolo
settore={}
for ex in EX:
    for r in leggi("stocks","ticker,sector",ex,{"in_universe":"eq.true"}):
        settore[(r["ticker"],ex)]=r.get("sector") or "Unknown"

# somme parziali dai fondamentali
partials={}
for ex in EX:
    for r in leggi("fundamentals","ticker,exchange,mkt_cap,rank_eps_gr,rank_rev_gr",ex):
        sec=settore.get((r["ticker"],ex))
        if not sec: continue
        k=(ex,sec)
        p=partials.setdefault(k,{"ew":0.0,"ewt":0.0,"rw":0.0,"rwt":0.0,"n":0})
        mc=r.get("mkt_cap")
        if mc:
            if r.get("rank_eps_gr") is not None:
                p["ew"]+=r["rank_eps_gr"]*mc; p["ewt"]+=mc
            if r.get("rank_rev_gr") is not None:
                p["rw"]+=r["rank_rev_gr"]*mc; p["rwt"]+=mc
        p["n"]+=1

ora=datetime.utcnow().isoformat()
righe=[{"exchange":ex,"sector":sec,"sum_eps_weighted":v["ew"],"sum_eps_weight":v["ewt"],
        "sum_rev_weighted":v["rw"],"sum_rev_weight":v["rwt"],"n_stocks":v["n"],
        "updated_at":ora} for (ex,sec),v in partials.items()]
ok=0
for i in range(0,len(righe),500):
    r=requests.post(U+"/rest/v1/sector_quintile_partials?on_conflict=exchange,sector",headers=HU,json=righe[i:i+500])
    if r.status_code in (200,201,204): ok+=len(righe[i:i+500])
    else: print("ERRORE %s: %s" % (r.status_code, r.text[:200]))
print("righe scritte: %d" % ok)

# verifica
r=requests.get(U+"/rest/v1/sector_quintile_partials",headers=H,
    params={"select":"updated_at","order":"updated_at.desc","limit":"1"})
d=r.json()
print("data piu' recente ora:", d[0]["updated_at"][:19] if d else "-")
from collections import Counter
r2=requests.get(U+"/rest/v1/sector_quintile_partials",headers=H,params={"select":"updated_at","limit":"1000"})
c=Counter(x["updated_at"][:10] for x in r2.json() if x.get("updated_at"))
print("distribuzione:", dict(c))
