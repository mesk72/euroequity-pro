import os, requests, json, re
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
d=json.load(open('/home/claude/dati210.json'))
def fuori(nome):
    t=(nome or "").upper()
    parole=set(re.findall(r"[A-Z0-9&]+",t))
    if parole & {"ETF","ETP","ETN","FUND","FUNDS","INDEX","INDEKS"}: return True
    if re.search(r"[a-z]ETF\b", nome or ""): return True
    if "INVEST" in parole: return True
    if re.search(r"\b(BANKINVEST|SYDINVEST|SPARINVEST|SPARINDEX|EGNSINVEST|MAJINVEST)\b",t): return True
    return False
back=[x for x in d if not fuori(x["company"])]
print("Reintegro %d titoli..." % len(back))
ok=0
for x in back:
    r=requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+x["ticker"],"exchange":"eq."+x["exchange"]},
        json={"in_universe":True})
    if r.status_code==204: ok+=1
print("  reintegrati: %d" % ok)
print()
print("=== VERIFICA su titoli chiave ===")
for tk,ex in [("NFLX","US"),("BLK","US"),("WT","US"),("SMT","LSE"),("ALLFG","AS"),
              ("1305","TSE"),("DKIGI","CPSE"),("NDI4KL1","CPSE")]:
    v=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"company,in_universe","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    if v: print("  %-10s %-46s %s" % (tk,(v[0].get('company') or '')[:46],
                "IN UNIVERSO" if v[0].get("in_universe") else "escluso"))
print()
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    tot+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("UNIVERSO TOTALE: %d titoli" % tot)
