import os, requests, csv, io
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').replace('x','').strip()
    if s in ("","-","NM","NA","n/a"): return None
    try: return float(s)
    except: return None
MAP={"BIT":"MIL","XTRA":"XETRA","ENXTPA":"PA","ENXTAM":"AS","BME":"MC","ENXTBR":"BR",
     "ENXTLS":"LS","WBAG":"VI","HLSE":"HE","ISE":"IR","ATSE":"GR","LSE":"LSE",
     "SWX":"SWX","OM":"OM","OB":"OB","CPSE":"CPSE"}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
tikr={}
for row in righe:
    t=(row.get("Ticker") or "").strip(); px=(row.get("Primary Exchange") or "").strip()
    ex=MAP.get(px)
    if t and ex:
        tikr[(t,ex)]={"pb":pn(row.get("LTM P/BVPS LTM")),"pe":pn(row.get("LTM P/E LTM"))}

fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,pe_trailing,pb","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break

print("=== confronto P/B: nostro vs TIKR, per mercato ===")
print("%-7s %7s %8s %9s %9s %9s" % ("EX","CONFR","UGUALI","x100","x1000","ALTRO"))
tot=defaultdict(lambda: defaultdict(int))
esempi=defaultdict(list)
for x in fu:
    k=(x["ticker"],x["exchange"]); t=tikr.get(k)
    if not t or t["pb"] is None or x.get("pb") is None or t["pb"]==0: continue
    ex=x["exchange"]; rap=x["pb"]/t["pb"]
    tot[ex]["n"]+=1
    if 0.9<rap<1.1: tot[ex]["ok"]+=1
    elif 90<rap<110:
        tot[ex]["x100"]+=1
        if len(esempi[ex])<3: esempi[ex].append((x["ticker"],x["pb"],t["pb"]))
    elif 900<rap<1100: tot[ex]["x1000"]+=1
    else: tot[ex]["altro"]+=1
for ex in sorted(tot,key=lambda e:-(tot[e]["x100"]+tot[e]["x1000"])):
    d=tot[ex]
    print("%-7s %7d %8d %9d %9d %9d" % (ex,d["n"],d["ok"],d["x100"],d["x1000"],d["altro"]))
    for e in esempi[ex]:
        print("        es. %-9s nostro=%s TIKR=%s" % e)
