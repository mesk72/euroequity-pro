import os, requests, csv, io
from collections import Counter, defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
print("=== valori di 'Primary Exchange' nel file ===")
c=Counter((x.get("Primary Exchange") or "?").strip() for x in righe)
for k,v in c.most_common(25): print("   %-16s %d" % (k,v))
