import os, requests
from datetime import datetime, timezone
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
print()
print("=== A) NEWS: quanto sono fresche? ===")
r=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","limit":"1"})
print("  righe in cache:", r.headers.get("content-range","?").split("/")[-1])
d=requests.get(U+"/rest/v1/news_cache",headers=H,
    params={"select":"ticker,title,published_at,fetched_at","order":"published_at.desc","limit":"6"}).json()
if isinstance(d,list) and d:
    print("  colonne:", list(d[0].keys()))
    for x in d[:5]:
        print("   %-9s %s  %s" % (x.get("ticker"),(x.get("published_at") or "?")[:16],(x.get("title") or "")[:52]))
    # quante nelle ultime 24h
    rc=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","published_at":"gte."+ (datetime.now(timezone.utc).replace(microsecond=0).isoformat()[:10]),"limit":"1"})
    print("  pubblicate da oggi:", rc.headers.get("content-range","?").split("/")[-1])
else:
    print("  ",d)
print()
print("=== B) REVERSE EARNINGS MODEL ===")
for t in ["implied_growth","reverse_dcf","implied_growth_us","reverse_earnings"]:
    rr=requests.get(U+"/rest/v1/"+t,headers={**H,"Prefer":"count=exact"},params={"select":"*","limit":"1"})
    if rr.status_code==200:
        n=rr.headers.get("content-range","?").split("/")[-1]
        print("  tabella %-20s ESISTE: %s righe" % (t,n))
        c=rr.json()
        if c: print("     colonne:", list(c[0].keys()))
