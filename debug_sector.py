import os, requests
from collections import Counter
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

GRUPPI=[("Europa",["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
        ("Stati Uniti",["US"]),("Canada",["TSX"]),("Giappone",["TSE"]),
        ("Hong Kong",["SEHK"]),("Australia",["ASX"]),("Corea",["KRX"]),("Singapore",["SGX"])]
TUTTI=[e for _,l in GRUPPI for e in l]
oggi=datetime.utcnow()+timedelta(hours=2)

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

dati={}
for ex in TUTTI:
    uni=leggi("stocks","ticker,company",ex,{"in_universe":"eq.true"})
    pre=leggi("latest_prices","ticker,price_date",ex)
    nomi={r["ticker"]:(r.get("company") or r["ticker"]) for r in uni}
    tick=set(nomi)
    dt={r["ticker"]:r.get("price_date") for r in pre if r["ticker"] in tick}
    dati[ex]={"uni":tick,"nomi":nomi,"date":dt,"assenti":sorted(tick-set(dt))}

tot_uni=sum(len(d["uni"]) for d in dati.values())
print("UNIVERSO TOTALE: %d titoli" % tot_uni)
print()
print("=== DISTRIBUZIONE PER DATA (tutto il sito) ===")
c=Counter(); mai=0
for ex in TUTTI:
    mai+=len(dati[ex]["assenti"])
    for d in dati[ex]["date"].values():
        if d: c[d]+=1
        else: mai+=1
for d,n in sorted(c.items(),reverse=True):
    g=(oggi.date()-datetime.strptime(d,"%Y-%m-%d").date()).days
    et="oggi" if g==0 else ("ieri" if g==1 else "%d giorni fa"%g)
    print("  %s  %-14s %5d titoli  %5.1f%%" % (d,et,n,n/tot_uni*100))
if mai: print("  %-10s %-14s %5d titoli  %5.1f%%" % ("mai scritti","",mai,mai/tot_uni*100))

print()
print("=== PER MERCATO ===")
print("%-14s %6s %7s %7s %7s %5s  %s" % ("MERCATO","TOT","31/07","30/07","+VECCHI","MAI","PREVALENTE"))
for nome,lista in GRUPPI:
    tot=sum(len(dati[e]["uni"]) for e in lista)
    cc=Counter(); mm=0
    for e in lista:
        mm+=len(dati[e]["assenti"])
        for d in dati[e]["date"].values():
            if d: cc[d]+=1
            else: mm+=1
    n31=cc.get("2026-07-31",0); n30=cc.get("2026-07-30",0)
    vecchi=sum(v for k,v in cc.items() if k<"2026-07-30")
    prev=cc.most_common(1)[0][0] if cc else "-"
    print("%-14s %6d %7d %7d %7d %5d  %s" % (nome,tot,n31,n30,vecchi,mm,prev))

print()
print("=== TITOLI MOLTO INDIETRO (oltre 7 giorni) ===")
lim=(oggi-timedelta(days=7)).strftime("%Y-%m-%d")
vecchi=[]
for ex in TUTTI:
    for tk,d in dati[ex]["date"].items():
        if d and d<lim: vecchi.append((d,tk,ex,dati[ex]["nomi"].get(tk,tk)))
vecchi.sort()
print("Totale: %d" % len(vecchi))
for d,tk,ex,az in vecchi:
    g=(oggi.date()-datetime.strptime(d,"%Y-%m-%d").date()).days
    print("  %s (%3d gg)  %-9s %-6s %s" % (d,g,tk,ex,az[:42]))

print()
print("=== MAI SCRITTI ===")
print("Totale: %d" % mai)
for ex in TUTTI:
    for tk in dati[ex]["assenti"]:
        print("  %-9s %-6s %s" % (tk,ex,dati[ex]["nomi"].get(tk,tk)[:42]))
