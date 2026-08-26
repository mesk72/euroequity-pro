import os, requests
from datetime import datetime, timezone, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
print()
print("=== NEWS ===")
d=requests.get(U+"/rest/v1/news_cache",headers=H,params={"select":"*","limit":"2"}).json()
if isinstance(d,list) and d:
    print("  colonne:", list(d[0].keys()))
    campo=[c for c in d[0] if "date" in c or "time" in c or "pub" in c or "created" in c]
    print("  campi temporali:",campo)
    if campo:
        c0=campo[0]
        u=requests.get(U+"/rest/v1/news_cache",headers=H,
            params={"select":"ticker,title,"+c0,"order":c0+".desc","limit":"5"}).json()
        for x in u: print("   %-9s %s  %s" % (x.get("ticker"),str(x.get(c0))[:16],(x.get("title") or "")[:50]))
        ieri=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
        rc=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
            params={"select":"ticker",c0:"gte."+ieri,"limit":"1"})
        print("  nelle ultime 24 ore:", rc.headers.get("content-range","?").split("/")[-1])
print()
print("=== REVERSE EARNINGS: dove sta il dato? ===")
f=requests.get(U+"/rest/v1/fundamentals",headers=H,params={"select":"*","limit":"1"}).json()
if f:
    imp=[c for c in f[0] if "impl" in c.lower() or "reverse" in c.lower() or "rev_dcf" in c.lower()]
    print("  colonne in fundamentals:", imp if imp else "nessuna colonna 'implied'")
    print("  tutte le colonne:", [c for c in f[0]][:30])
