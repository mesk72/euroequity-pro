import os, requests
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

print("=== 1. Struttura di news_cache ===")
r=requests.get(U+"/rest/v1/news_cache",headers=H,params={"select":"*","limit":"2"})
d=r.json()
if isinstance(d,list) and d:
    print("colonne:", list(d[0].keys()))
    for row in d:
        print("  esempio: ticker=%r region=%r fetched_at=%s" % (row.get("ticker"),row.get("region"),row.get("fetched_at")))
else:
    print("VUOTA o errore:", str(d)[:200])

print("\n=== 2. Quante righe in totale e quante nelle ultime 24h ===")
rc=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},params={"select":"ticker","limit":"1"})
print("righe totali:", rc.headers.get("content-range","?").split("/")[-1])
da=(datetime.utcnow()-timedelta(hours=24)).isoformat()
rc2=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","fetched_at":"gte."+da,"limit":"1"})
print("righe ultime 24h:", rc2.headers.get("content-range","?").split("/")[-1])

print("\n=== 3. Formato dei ticker presenti (campione) ===")
r3=requests.get(U+"/rest/v1/news_cache",headers=H,params={"select":"ticker,region","limit":"400"})
rows=r3.json()
if isinstance(rows,list) and rows:
    con_punto=[x["ticker"] for x in rows if x.get("ticker") and "." in x["ticker"]]
    senza=[x["ticker"] for x in rows if x.get("ticker") and "." not in x["ticker"]]
    print("  con punto: %d  -> esempi %s" % (len(con_punto), con_punto[:8]))
    print("  senza punto: %d -> esempi %s" % (len(senza), senza[:8]))
    from collections import Counter
    print("  regioni:", dict(Counter(x.get("region") for x in rows)))

print("\n=== 4. Ticker dei wallet: hanno notizie? ===")
rw=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"ticker,exchange,wallet","limit":"100"})
w=rw.json()
if isinstance(w,list) and w:
    print("  titoli in watchlist: %d" % len(w))
    from collections import Counter
    print("  per wallet:", dict(Counter(x.get("wallet") for x in w)))
    for x in w[:12]:
        tk=x["ticker"]
        rn=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
            params={"select":"ticker","ticker":"eq."+tk,"limit":"1"})
        n=rn.headers.get("content-range","0/0").split("/")[-1]
        print("     %-10s %-6s wallet=%s  notizie in cache: %s" % (tk,x["exchange"],x.get("wallet"),n))
else:
    print("  watchlist vuota o errore:", str(w)[:150])
