import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def n(params):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={**params,"select":"ticker","limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
print("=== CONTEGGI GLOBALI tabella stocks ===")
print("  in_universe = true :", n({"in_universe":"eq.true"}))
print("  in_universe = false:", n({"in_universe":"eq.false"}))
print("  in_universe NULL   :", n({"in_universe":"is.null"}))
print("  TOTALE righe       :", n({}))
print()
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
print("=== per exchange (in universo) ===")
tot=0
for ex in EX:
    v=n({"exchange":"eq."+ex,"in_universe":"eq.true"}); tot+=v
    print("  %-6s %5d" % (ex,v))
print("  SOMMA dei 23 exchange conosciuti: %d" % tot)
print()
print("=== esistono exchange NON nella nostra lista? ===")
r=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"exchange","in_universe":"eq.true","limit":"10000"})
d=r.json()
from collections import Counter
c=Counter(x["exchange"] for x in d if isinstance(x,dict))
altri={k:v for k,v in c.items() if k not in EX}
print("  righe lette:",len(d))
print("  exchange fuori lista:", altri if altri else "nessuno")
