import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

print("=== A. Le notizie sono legate al mercato giusto? ===")
for tk in ["ROP","SAN","BMY","UCB","COR"]:
    r=requests.get(U+"/rest/v1/news_cache",headers=H,
        params={"select":"ticker,exchange,company","ticker":"eq."+tk,"limit":"20"})
    rows=r.json()
    combo={}
    for x in rows:
        combo.setdefault((x.get("exchange"),x.get("company")),0)
        combo[(x.get("exchange"),x.get("company"))]+=1
    print("  %-5s -> %s" % (tk, combo))

print("\n=== B. Riproduco la chiamata che fa MyScreen ===")
# come costruisce MyScreen: "TICKER.EXCHANGE"
esempi=["ROP.SWX","AMGN.US","SAN.PA","5101.TSE"]
print("  parametro inviato:", ",".join(esempi))
# come lo interpreta l'endpoint: split('.')[0]
interpretati=[p.split(".")[0] for p in esempi]
print("  ticker cercati (dopo split sul punto):", interpretati)
r=requests.get(U+"/rest/v1/news_cache",headers=H,
    params={"select":"ticker,exchange","ticker":"in.("+",".join(interpretati)+")","limit":"100"})
rows=r.json()
from collections import Counter
print("  risultati:", dict(Counter((x["ticker"],x.get("exchange")) for x in rows)))

print("\n=== C. Caso critico: ticker con il punto dentro (es. CAR.UN.TSX) ===")
r=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"ticker,exchange","limit":"200"})
w=r.json()
con_punto=[x for x in w if "." in x["ticker"]]
print("  titoli in watchlist col punto nel ticker: %d -> %s" % (len(con_punto),[x["ticker"] for x in con_punto][:10]))
for x in con_punto[:5]:
    param="%s.%s" % (x["ticker"],x["exchange"])
    cercato=param.split(".")[0]
    print("     wallet manda %-14s -> endpoint cerca %-8s (SBAGLIATO se diverso da %s)" % (param,cercato,x["ticker"]))

print("\n=== D. La pagina News come chiama l'endpoint? ===")
for reg in ["americas","europe","asia"]:
    rc=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","region":"eq."+reg,"limit":"1"})
    print("  region=%-9s righe: %s" % (reg,rc.headers.get("content-range","?").split("/")[-1]))
