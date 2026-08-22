import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== titoli chiave ===")
for tk,ex,atteso in [("NFLX","US","dentro"),("BLK","US","dentro"),("WT","US","dentro"),
                     ("SMT","LSE","dentro"),("ALLFG","AS","dentro"),("BST","US","dentro"),
                     ("1305","TSE","FUORI"),("DKIGI","CPSE","FUORI"),("NDI4KL1","CPSE","FUORI")]:
    v=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"company,in_universe","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    if not v: print("  %-10s %-4s NON TROVATO" % (tk,ex)); continue
    stato="dentro" if v[0].get("in_universe") else "FUORI"
    print("  %-10s %-4s %-44s %-7s (atteso %s) %s" % (tk,ex,(v[0].get('company') or '')[:44],
          stato,atteso,"OK" if stato==atteso else "DA CONTROLLARE"))
print()
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=n
    print("  %-6s %4d" % (ex,n))
print()
print("UNIVERSO TOTALE: %d" % tot)
