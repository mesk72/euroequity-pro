import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

print("=== universo attuale per exchange ===")
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=n
    print("  %-6s %5d" % (ex,n))
print("  TOTALE %d" % tot)
print()
print("=== titoli FUORI universo che hanno prezzi recenti (quindi lavoravano) ===")
# se un titolo ha prezzi scritti di recente ma e' fuori universo, e' uscito DOPO
fuori=[];off=0
while True:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company","in_universe":"eq.false","limit":"1000","offset":str(off)})
    b=r.json()
    if not isinstance(b,list) or not b: break
    fuori+=b; off+=1000
    if len(b)<1000: break
print("  fuori universo totali:", len(fuori))
con_prezzi=[]
for x in fuori[:400]:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq."+x["ticker"],"exchange":"eq."+x["exchange"],
                "date":"gte.2026-07-01","limit":"1"})
    n=int(rc.headers.get("content-range","0/0").split("/")[-1])
    if n>0: con_prezzi.append((x["ticker"],x["exchange"],(x.get("company") or "")[:34],n))
print("  di cui con prezzi da luglio in poi (campione di 400):", len(con_prezzi))
for t in con_prezzi[:30]: print("    %-10s %-5s %-34s %d righe da luglio" % t)
