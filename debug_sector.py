import os, requests, csv, io
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None

# TIKR: fonte autorevole
tikr={}
for f in ["tikr_eu_latest.csv","tikr_na_latest.csv"]:
    r=requests.get(U+"/storage/v1/object/tikr-uploads/"+f,headers=H,timeout=150)
    if r.status_code!=200: continue
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))):
        t=(row.get("Ticker") or "").strip()
        v=pn(row.get("Last Mkt Cap",""))
        if t and v:
            base=t.split(".")[0]
            tikr[base]=v
print("TIKR: %d titoli" % len(tikr))

def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
st=tutte("stocks","ticker,exchange,company,in_universe")
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}

SOSPETTI=["OM","PA","MIL","XETRA","LSE","SWX","AT","AIM","NGM"]
print()
print("=== TITOLI FUORI UNIVERSO che rientrerebbero con il valore TIKR corretto ===")
# soglie indicative attuali
SOGLIA={"OM":300,"PA":300,"MIL":300,"XETRA":300,"LSE":300,"SWX":300}
rientro=defaultdict(list)
for x in st:
    if x.get("in_universe"): continue
    ex=x["exchange"]
    if ex not in SOSPETTI: continue
    nostro=mc.get((x["ticker"],x["exchange"]))
    vero=tikr.get(x["ticker"])
    if vero is None: continue
    if nostro is not None and vero/max(nostro,0.0001)>500:
        rientro[ex].append((x["ticker"],(x.get("company") or "")[:30],nostro,vero))
tot=0
for ex in sorted(rientro):
    lst=rientro[ex]; tot+=len(lst)
    print("  %-6s %4d titoli con valore letto 1000x troppo piccolo" % (ex,len(lst)))
    for t in sorted(lst,key=lambda x:-x[3])[:4]:
        print("       %-9s %-30s nostro=%.3f  vero=%.0f MM" % t)
print()
print("TOTALE candidati al rientro: %d" % tot)
print()
print("=== quanti supererebbero una soglia di 300 MM ===")
sopra=sum(1 for ex in rientro for t in rientro[ex] if t[3]>=300)
print("  sopra 300 MM: %d" % sopra)
print("  sotto  300 MM: %d (resterebbero fuori a ragione)" % (tot-sopra))
