import os, requests
from datetime import datetime, timezone, timedelta
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
print()
print("=== quando e' stata scaricata l'ultima notizia? ===")
d=requests.get(U+"/rest/v1/news_cache",headers=H,
    params={"select":"ticker,title,pub_date,fetched_at","order":"fetched_at.desc","limit":"8"}).json()
for x in d: print("   fetch=%s  pub=%-26s %-8s %s" % (str(x.get("fetched_at"))[:16],str(x.get("pub_date"))[:26],x.get("ticker"),(x.get("title") or "")[:40]))
print()
ieri=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
for ore,eti in [(6,"6 ore"),(24,"24 ore"),(72,"3 giorni")]:
    t=(datetime.now(timezone.utc)-timedelta(hours=ore)).isoformat()
    r=requests.get(U+"/rest/v1/news_cache",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","fetched_at":"gte."+t,"limit":"1"})
    print("  scaricate nelle ultime %-10s %s" % (eti, r.headers.get("content-range","?").split("/")[-1]))
print()
print("=== il cron delle notizie sta girando? ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"script_name,created_at","script_name":"ilike.*news*","order":"created_at.desc","limit":"5"}).json()
print("  log news:",r if r else "nessuno")
