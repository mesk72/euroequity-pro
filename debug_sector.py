import requests
B="https://forwardalpha.pro/api/news-cache"

print("=== Wallet farmaceutico: le notizie sono solo dei titoli giusti? ===")
w="ROP.SWX,SAN.PA,BMY.US,UCB.BR,AMGN.US,GSK.LSE"
r=requests.get(B+"?tickers="+w+"&limit=200",timeout=60)
items=r.json().get("items",[])
from collections import Counter
c=Counter((i["ticker"],i.get("exchange"),i.get("company")) for i in items)
print("  notizie totali: %d" % len(items))
for k,v in sorted(c.items()):
    print("    %-6s %-5s %-34s %2d" % (k[0],k[1],(k[2] or "")[:34],v))

attesi={("ROP","SWX"),("SAN","PA"),("BMY","US"),("UCB","BR"),("AMGN","US"),("GSK","LSE")}
intrusi=[k for k in c if (k[0],k[1]) not in attesi]
print("\n  INTRUSI (societa' omonime su altri mercati): %s" % (intrusi if intrusi else "NESSUNO"))

print("\n=== La pagina News per regione funziona ancora? ===")
for reg in ["americas","europe","asia"]:
    r=requests.get(B+"?region="+reg+"&limit=500",timeout=60)
    n=len(r.json().get("items",[]))
    print("  region=%-9s %d notizie" % (reg,n))

print("\n=== Ticker con il punto dentro (ACO.X, GO.U) ===")
r=requests.get(B+"?tickers=ACO.X.TSX,GO.U.TSX&limit=50",timeout=60)
items=r.json().get("items",[])
print("  notizie: %d -> %s" % (len(items), Counter((i["ticker"],i.get("exchange")) for i in items)))
