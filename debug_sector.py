import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
RIENTRANO=[
 ("NFLX","US","Netflix — 'etf' dentro N-ETF-lix"),
 ("BLK","US","BlackRock Inc., la societa' di gestione quotata"),
 ("WT","US","WisdomTree Inc., emittente quotato"),
 ("JUP","LSE","Jupiter Fund Management, gestore quotato"),
 ("VEIL","LSE","Vietnam Enterprise — 'etn' dentro Ent-ERPRISE"),
 ("FRT","US","Federal Realty Investment Trust, REIT"),
 ("PMT","US","PennyMac Mortgage Investment Trust, REIT"),
 ("UHT","US","Universal Health Realty Income Trust, REIT"),
 ("SREI","LSE","Schroder Real Estate Investment Trust, REIT"),
 ("SWDR","US","Starwood Real Estate Income Trust, REIT"),
]
print("=== RIENTRANO: societa' operative e REIT esclusi per errore ===")
for tk,ex,motivo in RIENTRANO:
    r=requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+tk,"exchange":"eq."+ex},json={"in_universe":True})
    v=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"company,in_universe","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    ok=v[0].get("in_universe") if v else None
    print("  %-6s %-4s %-52s -> %s" % (tk,ex,motivo,"OK" if ok else "FALLITO"))
print()
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    tot+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("UNIVERSO: %d titoli" % tot)
