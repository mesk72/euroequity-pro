import os, requests, csv, io
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None

# suffisso TIKR -> nostro exchange
SUF={".MI":"MIL",".DE":"XETRA",".PA":"PA",".AS":"AS",".MC":"MC",".BR":"BR",".LS":"LS",
     ".VI":"VI",".HE":"HE",".IR":"IR",".AT":"GR",".L":"LSE",".SW":"SWX",".ST":"OM",
     ".OL":"OB",".CO":"CPSE"}
tikr={}
for f in ["tikr_eu_latest.csv","tikr_na_latest.csv"]:
    r=requests.get(U+"/storage/v1/object/tikr-uploads/"+f,headers=H,timeout=150)
    if r.status_code!=200: continue
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))):
        t=(row.get("Ticker") or "").strip()
        v=pn(row.get("Last Mkt Cap",""))
        if not t or not v: continue
        for suf,ex in SUF.items():
            if t.endswith(suf):
                tikr[(t[:-len(suf)],ex)]=v
                break
        else:
            tikr[(t,"US")]=v
print("TIKR abbinato per (ticker, mercato): %d" % len(tikr))

fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,mkt_cap","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break

sbagliati=[]; ok=0; mancanti=0
for x in fu:
    k=(x["ticker"],x["exchange"])
    vero=tikr.get(k)
    if vero is None: mancanti+=1; continue
    nostro=x.get("mkt_cap")
    if nostro is None or nostro<=0:
        sbagliati.append((x["ticker"],x["exchange"],nostro,vero)); continue
    rap=vero/nostro
    if 0.95<rap<1.05: ok+=1
    elif 500<rap<2000: sbagliati.append((x["ticker"],x["exchange"],nostro,vero))
print("  corretti: %d | da correggere: %d | non in TIKR: %d" % (ok,len(sbagliati),mancanti))
print()
print("=== esempi di correzione (abbinamento per ticker E mercato) ===")
for t in sorted(sbagliati,key=lambda x:-x[3])[:12]:
    print("   %-10s %-6s  %8s -> %10.0f MM" % t)
import json
open("/tmp/sbagliati.json","w").write(json.dumps(sbagliati))
print()
print("salvati %d titoli da correggere" % len(sbagliati))
