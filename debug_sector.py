import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/sector_quintile_partials",headers=H,
    params={"select":"exchange,sector,updated_at","limit":"1000"})
d=r.json()
print("righe totali:", len(d))
c=Counter(x["updated_at"][:10] for x in d if x.get("updated_at"))
print("distribuzione per data di aggiornamento:")
for k,v in sorted(c.items(),reverse=True): print("  %s : %d righe" % (k,v))
print()
print("per exchange, data piu' recente:")
per_ex={}
for x in d:
    ex=x["exchange"]; u=(x.get("updated_at") or "")[:10]
    if ex not in per_ex or u>per_ex[ex]: per_ex[ex]=u
for ex in sorted(per_ex): print("  %-6s %s" % (ex,per_ex[ex]))
