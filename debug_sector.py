import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HD={**H,"Prefer":"return=minimal"}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
DATA="2026-07-30"

def conta(ex):
    r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq."+DATA,"limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])

print("PRIMA:")
prima={ex:conta(ex) for ex in EU}
tot_prima=sum(prima.values())
for ex,n in prima.items():
    if n: print("  %-6s %4d" % (ex,n))
print("  TOTALE %d" % tot_prima)

print("\nCANCELLAZIONE (solo exchange europei, solo data %s):" % DATA)
for ex in EU:
    if not prima[ex]: continue
    r=requests.delete(U+"/rest/v1/prices_eod",headers=HD,
        params={"exchange":"eq."+ex,"date":"eq."+DATA})
    print("  %-6s HTTP %s" % (ex, r.status_code))

print("\nDOPO:")
dopo={ex:conta(ex) for ex in EU}
tot_dopo=sum(dopo.values())
for ex,n in dopo.items():
    if n: print("  %-6s %4d  <-- RESIDUO" % (ex,n))
print("  TOTALE %d" % tot_dopo)
print("\nCancellate: %d righe" % (tot_prima-tot_dopo))

print("\nVERIFICA su 3 titoli (ultima data rimasta):")
for tk,ex in [("AKTIA","HE"),("BURE","OM"),("ALMB","CPSE")]:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,
                "order":"date.desc","limit":"2"})
    print("  %-6s.%-5s %s" % (tk,ex,[(x["date"],x["adj_close"]) for x in r.json()]))

print("\nCONTROLLO che nessun ALTRO mercato sia stato toccato:")
for ex in ["US","TSX","TSE","SEHK","ASX","KRX","SGX"]:
    r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq."+DATA,"limit":"1"})
    print("  %-6s righe al %s: %s" % (ex,DATA,r.headers.get("content-range","?").split("/")[-1]))
