import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def n(ex,uni="true"):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq."+uni,"limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
EU=["MIL","XETRA","PA","LSE","SWX","OM","OB","CPSE","AS","MC","BR","LS","VI","HE","IR","GR"]
print("=== quanti titoli per mercato europeo ADESSO ===")
for ex in EU: print("  %-6s %4d" % (ex,n(ex)))
print()
print("=== gli score sono calcolati solo sui titoli in universo? ===")
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,value_score","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break
st=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,in_universe","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    st+=b; off+=1000
    if len(b)<1000: break
uni=set((x["ticker"],x["exchange"]) for x in st if x.get("in_universe"))
con_score=[x for x in fu if x.get("value_score") is not None]
fuori=[x for x in con_score if (x["ticker"],x["exchange"]) not in uni]
print("  righe fundamentals totali :", len(fu))
print("  con Value Score           :", len(con_score))
print("  di cui FUORI universo     :", len(fuori), "<-- non dovrebbero averlo")
for x in fuori[:8]: print("      %-10s %s" % (x["ticker"],x["exchange"]))
