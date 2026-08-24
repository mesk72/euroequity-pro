import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
o=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"sector","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    o+=b; off+=1000
    if len(b)<1000: break
c=Counter((x.get("sector") or "(vuoto)") for x in o)
print("=== settori nel database, mercato USA ===")
for k,v in c.most_common(): print("   %-34s %4d" % (k,v))
print()
print("=== come si chiama la tabella dei quintili di settore? ===")
r=requests.get(U+"/rest/v1/sector_quintile_partials",headers=H,params={"select":"*","limit":"3"})
d=r.json()
if isinstance(d,list) and d:
    print("  colonne:",list(d[0].keys()))
    for x in d: print("   ",x)
