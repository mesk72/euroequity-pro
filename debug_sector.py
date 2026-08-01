import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}

r=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,exchange,company,in_universe","ticker":"eq.IIP.UN","exchange":"eq.TSX"})
print("PRIMA:", r.json())
r2=requests.patch(U+"/rest/v1/stocks",headers=HP,
    params={"ticker":"eq.IIP.UN","exchange":"eq.TSX"},json={"in_universe":False})
print("PATCH HTTP:", r2.status_code)
r3=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,exchange,company,in_universe","ticker":"eq.IIP.UN","exchange":"eq.TSX"})
print("DOPO:", r3.json())

# universo aggiornato
tot=0
for ex in ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]:
    rc=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","in_universe":"eq.true","exchange":"eq."+ex,"limit":"1"})
    tot+=int(rc.headers.get("content-range","0/0").split("/")[-1])
print("\nUniverso attivo ora: %d titoli" % tot)
