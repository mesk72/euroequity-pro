import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
NOMI={"MIL":"Milano","XETRA":"Francoforte","PA":"Parigi","AS":"Amsterdam","MC":"Madrid",
      "BR":"Bruxelles","LS":"Lisbona","VI":"Vienna","HE":"Helsinki","IR":"Dublino",
      "GR":"Atene","LSE":"Londra","SWX":"Zurigo","OM":"Stoccolma","OB":"Oslo","CPSE":"Copenaghen"}
print("=== SITUAZIONE ATTUALE nell'universo ===")
print("%-14s %-6s %8s   %s" % ("MERCATO","COD","IN UNIV","criterio che sembra applicato"))
for ex in EU:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1])
    crit = "TUTTI sopra soglia" if n>100 else ("primi 100 (esatto)" if n==100 else "tutti quelli disponibili")
    print("%-14s %-6s %8d   %s" % (NOMI[ex],ex,n,crit))
print()
print("=== quanti titoli avrebbe ogni mercato con soglia 300 MM USD (dati attuali) ===")
print("%-14s %8s %10s" % ("MERCATO","IN UNIV","sopra 300"))
for ex in EU:
    fu=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/fundamentals",headers=H,
            params={"select":"ticker,mkt_cap","exchange":"eq."+ex,"limit":"1000","offset":str(off)}).json()
        if not isinstance(b,list) or not b: break
        fu+=b; off+=1000
        if len(b)<1000: break
    sopra=sum(1 for x in fu if x.get("mkt_cap") and x["mkt_cap"]>=300)
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1])
    print("%-14s %8d %10d" % (NOMI[ex],n,sopra))
