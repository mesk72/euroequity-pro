import os, requests, csv, io
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None
MAP={"BIT":"MIL","XTRA":"XETRA","ENXTPA":"PA","ENXTAM":"AS","BME":"MC","ENXTBR":"BR",
     "ENXTLS":"LS","WBAG":"VI","HLSE":"HE","ISE":"IR","ATSE":"GR","LSE":"LSE",
     "SWX":"SWX","OM":"OM","OB":"OB","CPSE":"CPSE"}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
tikr={}
for row in righe:
    t=(row.get("Ticker") or "").strip()
    px=(row.get("Primary Exchange") or "").strip()
    v=pn(row.get("Last Mkt Cap",""))
    ex=MAP.get(px)
    if t and ex and v: tikr[(t,ex)]=(v,(row.get("Company Name") or ""),(row.get("Sector") or ""))
print("TIKR abbinato correttamente: %d titoli" % len(tikr))

st=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,in_universe","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    st+=b; off+=1000
    if len(b)<1000: break

SOGLIA=["MIL","XETRA","PA","LSE","SWX","OM","OB","CPSE"]   # soglia 300 MM
CENTO=["AS","MC","BR","LS","VI","HE","IR","GR"]            # primi 100
ESCL=["ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","INVESCO",
      "SPDR","WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","MSCI","INDEX","AMUNDI","OBX"]
def fondo(*n):
    return any(any(k in (x or "").upper() for k in ESCL) for x in n)

print()
print("=== A) titoli FUORI universo che dovrebbero RIENTRARE ===")
rientro=defaultdict(list)
for x in st:
    if x.get("in_universe"): continue
    k=(x["ticker"],x["exchange"])
    if k not in tikr: continue
    v,nome,sett=tikr[k]
    if fondo(nome,x.get("company")): continue
    if x["exchange"] in SOGLIA and v>=300:
        rientro[x["exchange"]].append((x["ticker"],nome[:34],v))
tot=0
for ex in sorted(rientro,key=lambda e:-len(rientro[e])):
    print("  %-6s %3d titoli" % (ex,len(rientro[ex]))); tot+=len(rientro[ex])
    for t in sorted(rientro[ex],key=lambda x:-x[2])[:5]:
        print("      %-10s %-34s %8.0f MM" % t)
print("  TOTALE da reintegrare: %d" % tot)
print()
print("=== B) titoli DENTRO che NON dovrebbero esserci (sotto soglia) ===")
esci=defaultdict(int)
for x in st:
    if not x.get("in_universe"): continue
    k=(x["ticker"],x["exchange"])
    if k not in tikr: continue
    v,nome,sett=tikr[k]
    if x["exchange"] in SOGLIA and v<300: esci[x["exchange"]]+=1
print("  ", dict(esci), "-> totale", sum(esci.values()))
import json
open("/tmp/rientro.json","w").write(json.dumps({k:v for k,v in rientro.items()}))
