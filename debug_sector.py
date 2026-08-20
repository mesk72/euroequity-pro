import os, requests, csv, io
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').replace('x','').replace('%','').strip()
    if s in ("","-","NM","NA","n/a","NaN"): return None
    try: return float(s)
    except: return None
MAP={"BIT":"MIL","XTRA":"XETRA","ENXTPA":"PA","ENXTAM":"AS","BME":"MC","ENXTBR":"BR",
     "ENXTLS":"LS","WBAG":"VI","HLSE":"HE","ISE":"IR","ATSE":"GR","LSE":"LSE",
     "SWX":"SWX","OM":"OM","OB":"OB","CPSE":"CPSE"}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
tikr={}
for row in csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))):
    t=(row.get("Ticker") or "").strip(); ex=MAP.get((row.get("Primary Exchange") or "").strip())
    if t and ex:
        tikr[(t,ex)]={"pe":pn(row.get("LTM P/E LTM")),"pef":pn(row.get("Mean Fwd P/E NTM")),
                      "pb":pn(row.get("LTM P/BVPS LTM"))}
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break

diff=defaultdict(int); esempi=[]
tot_confr=0
for x in fu:
    t=tikr.get((x["ticker"],x["exchange"]))
    if not t: continue
    tot_confr+=1
    cambia=False
    for campo,nostro_k in [("pe","pe_trailing"),("pef","pe_forward"),("pb","pb")]:
        n=x.get(nostro_k); v=t[campo]
        if v is None and n is None: continue
        if v is None or n is None: cambia=True; continue
        if abs(n-v)>max(0.01,abs(v)*0.02): cambia=True
    if cambia:
        diff[x["exchange"]]+=1
        if len(esempi)<12:
            esempi.append((x["ticker"],x["exchange"],
                (x.get("pe_trailing"),x.get("pe_forward"),x.get("pb")),
                (t["pe"],t["pef"],t["pb"])))
print("Titoli confrontabili con TIKR EU: %d" % tot_confr)
print("Titoli che CAMBIEREBBERO: %d" % sum(diff.values()))
print()
for ex in sorted(diff,key=lambda e:-diff[e]):
    print("   %-6s %4d" % (ex,diff[ex]))
print()
print("=== esempi (nostro -> TIKR), formato PE/PEfwd/PB ===")
for tk,ex,nostro,vero in esempi:
    print("  %-10s %-5s %-28s -> %s" % (tk,ex,str(nostro),str(vero)))
