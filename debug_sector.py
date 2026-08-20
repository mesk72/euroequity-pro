import os, requests, csv, io
from collections import Counter, defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').replace('x','').strip()
    if s in ("","-","NM","NA","n/a","NaN"): return None
    try: return float(s)
    except: return None
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_apac_latest.csv",headers=H,timeout=200)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
print("tikr_apac_latest.csv: %d righe" % len(righe))
print("colonne:", list(righe[0].keys())[:10])
print()
print("=== valori di Primary Exchange ===")
c=Counter((x.get("Primary Exchange") or "?").strip() for x in righe)
for k,v in c.most_common(15): print("   %-12s %d" % (k,v))
print()
print("=== esempi ===")
for x in righe[:4]:
    print("   %-12s %-32s %s" % (x.get("Ticker"),(x.get("Company Name") or "")[:32],x.get("Last Mkt Cap")))
print()
print("=== l'Asia ha lo stesso difetto di scala? ===")
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,pb","exchange":"in.(TSE,SEHK,ASX,KRX,SGX)","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break
d=defaultdict(lambda: defaultdict(int))
for x in fu:
    v=x.get("pb")
    if v is None: d[x["exchange"]]["senza"]+=1
    elif v<0.01: d[x["exchange"]]["quasi_zero"]+=1
    elif v>50: d[x["exchange"]]["oltre_50"]+=1
    else: d[x["exchange"]]["normale"]+=1
print("%-7s %9s %11s %10s %8s" % ("EX","NORMALE","QUASI ZERO","OLTRE 50","SENZA"))
for ex in sorted(d):
    x=d[ex]
    print("%-7s %9d %11d %10d %8d" % (ex,x["normale"],x["quasi_zero"],x["oltre_50"],x["senza"]))
