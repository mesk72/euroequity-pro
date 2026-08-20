import os, requests
from collections import Counter, defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
st=tutte("stocks","ticker,exchange,in_universe")
fu=tutte("fundamentals","ticker,exchange,value_score,growth_score,combined_rank,pe_trailing,pb")
uni=set((x["ticker"],x["exchange"]) for x in st if x.get("in_universe"))
print("UNIVERSO: %d titoli" % len(uni))
f={(x["ticker"],x["exchange"]):x for x in fu}
cv=cg=cc=0
for k in uni:
    x=f.get(k)
    if not x: continue
    if x.get("value_score") is not None: cv+=1
    if x.get("growth_score") is not None: cg+=1
    if x.get("combined_rank") is not None: cc+=1
print("  con Value Score : %d (%.1f%%)" % (cv,cv/len(uni)*100))
print("  con Growth Score: %d (%.1f%%)" % (cg,cg/len(uni)*100))
print("  con Best Score  : %d (%.1f%%)" % (cc,cc/len(uni)*100))
print()
print("=== verifica: i titoli corretti hanno ora punteggi sensati? ===")
print("%-10s %-5s %8s %6s %7s %7s" % ("TICKER","EX","PE","PB","VALUE","GROWTH"))
for tk,ex in [("KRAB","OB"),("GSF","OB"),("FOAMIT","HE"),("OLE","MC"),
              ("MAERSK B","CPSE"),("CARL B","CPSE"),("NSKOG","OB"),("NEOBO","OM")]:
    x=f.get((tk,ex))
    if not x: print("%-10s %-5s  assente" % (tk,ex)); continue
    print("%-10s %-5s %8s %6s %7s %7s" % (tk,ex,x.get("pe_trailing"),x.get("pb"),
        x.get("value_score"),x.get("growth_score")))
