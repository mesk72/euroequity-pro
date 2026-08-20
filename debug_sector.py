import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o

print("=== A) Danimarca e Norvegia: riporto ai primi 100 per capitalizzazione ===")
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
st=tutte("stocks","ticker,exchange,company,in_universe")
for ex,nome in [("CPSE","Danimarca"),("OB","Norvegia")]:
    dentro=[x for x in st if x["exchange"]==ex and x.get("in_universe")]
    with_mc=[(x,mc.get((x["ticker"],ex)) or 0) for x in dentro]
    with_mc.sort(key=lambda z:-z[1])
    tieni=set(x["ticker"] for x,_ in with_mc[:100])
    escono=[x for x,_ in with_mc[100:]]
    print("  %-10s in universo %d -> tengo i primi 100, escono %d" % (nome,len(dentro),len(escono)))
    for x in escono:
        requests.patch(U+"/rest/v1/stocks",headers=HP,
            params={"ticker":"eq."+x["ticker"],"exchange":"eq."+ex},json={"in_universe":False})
        print("      esce %-10s %-34s %s MM" % (x["ticker"],(x.get("company") or "")[:34],mc.get((x["ticker"],ex))))

print()
print("=== B) azzero gli score dei titoli FUORI universo ===")
st2=tutte("stocks","ticker,exchange,in_universe")
uni=set((x["ticker"],x["exchange"]) for x in st2 if x.get("in_universe"))
fu2=tutte("fundamentals","ticker,exchange,value_score,growth_score,combined_rank")
da_azzerare=[x for x in fu2
             if (x["ticker"],x["exchange"]) not in uni
             and (x.get("value_score") is not None or x.get("growth_score") is not None
                  or x.get("combined_rank") is not None)]
print("  titoli fuori universo con punteggi: %d" % len(da_azzerare))
lotto=[{"ticker":x["ticker"],"exchange":x["exchange"],
        "value_score":None,"growth_score":None,"combined_rank":None} for x in da_azzerare]
ok=0
for i in range(0,len(lotto),200):
    w=requests.post(U+"/rest/v1/fundamentals?on_conflict=ticker,exchange",headers=HU,json=lotto[i:i+200],timeout=120)
    if w.status_code in (200,201,204): ok+=len(lotto[i:i+200])
print("  azzerati: %d" % ok)

print()
print("=== VERIFICA ===")
for ex in ["MIL","XETRA","PA","LSE","SWX","OM","OB","CPSE","BR","HE","GR"]:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    print("  %-6s %4s" % (ex,r.headers.get("content-range","?").split("/")[-1]))
tot=0
for ex in ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    tot+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("\n  UNIVERSO TOTALE: %d" % tot)
