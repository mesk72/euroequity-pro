import os, requests
from datetime import datetime, timezone, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== NEWS: fetched_at e' una data vera? ===")
d=requests.get(U+"/rest/v1/news_cache",headers=H,
    params={"select":"ticker,title,pub_date,fetched_at","order":"fetched_at.desc","limit":"6"}).json()
for x in d: print("   %-8s fetch=%s  pub=%-22s %s" % (x.get("ticker"),str(x.get("fetched_at"))[:16],str(x.get("pub_date"))[:22],(x.get("title") or "")[:38]))
ieri=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
rc=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","fetched_at":"gte."+ieri,"limit":"1"})
print("  scaricate nelle ultime 24h:", rc.headers.get("content-range","?").split("/")[-1])
print()
print("=== REVERSE EARNINGS MODEL ===")
for campo in ["implied_growth","implied_growth_10y"]:
    rc=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker",campo:"not.is.null","limit":"1"})
    print("  %-20s valorizzato su %s righe" % (campo, rc.headers.get("content-range","?").split("/")[-1]))
d2=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,exchange,implied_growth,implied_growth_10y,updated_at","implied_growth":"not.is.null",
            "order":"mkt_cap.desc","limit":"8"}).json()
print()
print("  esempi (maggiori capitalizzazioni):")
for x in d2: print("   %-8s %-4s implicita=%-8s a10a=%-8s aggiornato=%s" % (
    x.get("ticker"),x.get("exchange"),x.get("implied_growth"),x.get("implied_growth_10y"),str(x.get("updated_at"))[:16]))
print()
print("=== chi calcola implied_growth? cerco nel repository ===")
