import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
print("=== universo per exchange ===")
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=n
print("  totale universo:",tot)
print()
print("=== quanti ne restituisce l'API Global? ===")
r=requests.get("https://forwardalpha.pro/api/db/stocks?exchanges="+",".join(EX),timeout=180)
d=r.json(); serviti=d.get("stocks",[])
print("  API Global:",len(serviti))
print()
print("=== dove si perdono? confronto per exchange ===")
from collections import Counter
c=Counter(x.get("exchange") for x in serviti)
print("%-7s %8s %8s %8s" % ("EX","UNIVERSO","SERVITI","MANCANO"))
for ex in EX:
    r2=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    u=int(r2.headers.get("content-range","0/0").split("/")[-1])
    s=c.get(ex,0)
    if u!=s: print("%-7s %8d %8d %8d" % (ex,u,s,u-s))
print()
print("=== quanti hanno un prezzo nella vista? ===")
mv=0
for ex in EX:
    r3=requests.get(U+"/rest/v1/latest_prices_mv",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"limit":"1"})
    mv+=int(r3.headers.get("content-range","0/0").split("/")[-1])
print("  righe nella vista prezzi:",mv)
