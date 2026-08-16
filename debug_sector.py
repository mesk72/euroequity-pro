import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
uni=[];off=0
while True:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,company","exchange":"eq.MIL","in_universe":"eq.true","limit":"1000","offset":str(off)})
    b=r.json()
    if not isinstance(b,list) or not b: break
    uni+=b; off+=1000
    if len(b)<1000: break
print("Titoli italiani nel nostro universo:", len(uni))

f=[];off=0
while True:
    r=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,mkt_cap","exchange":"eq.MIL","limit":"1000","offset":str(off)})
    b=r.json()
    if not isinstance(b,list) or not b: break
    f+=b; off+=1000
    if len(b)<1000: break
mc={x["ticker"]:x.get("mkt_cap") for x in f}
tick={x["ticker"] for x in uni}
val=[(t,mc[t]) for t in tick if mc.get(t)]
tot=sum(v for _,v in val)
print("con capitalizzazione disponibile:", len(val))
print()
print("mkt_cap e' in MILIONI di euro")
print("SOMMA: %.0f milioni = %.2f miliardi di euro" % (tot, tot/1000))
print("        = %.3f trilioni di euro" % (tot/1e6))
print("        = %.3f trilioni di dollari (cambio 1.17)" % (tot/1e6*1.17))
print()
print("Prime 10 per capitalizzazione (milioni di euro):")
nome={x["ticker"]:(x.get("company") or "") for x in uni}
for t,v in sorted(val,key=lambda x:-x[1])[:10]:
    print("   %-8s %-34s %10.0f" % (t,nome[t][:34],v))
