import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None
SUF={".ST":"OM",".OL":"OB",".CO":"CPSE",".HE":"HE"}
tikr={}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
for row in righe:
    t=(row.get("Ticker") or "").strip(); v=pn(row.get("Last Mkt Cap",""))
    if not t or not v: continue
    for suf,ex in SUF.items():
        if t.endswith(suf): tikr[(t[:-len(suf)],ex)]=(v,(row.get("Company Name") or "")); break
print("TIKR nordici: %d titoli" % len(tikr))
print()
ESCL=["ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","INVESCO",
      "SPDR","WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","MSCI","INDEX","AMUNDI"]
def e_fondo(nome):
    n=(nome or "").upper()
    return any(k in n for k in ESCL)

fuori=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,sector","in_universe":"eq.false",
                "exchange":"in.(OM,OB,CPSE,HE)","limit":"1000","offset":str(off)}).json()
    if not isinstance(b,list) or not b: break
    fuori+=b; off+=1000
    if len(b)<1000: break
print("esclusi nordici: %d" % len(fuori))
print()
cand=[]; fondi=0; non_tikr=0
for x in fuori:
    k=(x["ticker"],x["exchange"])
    if k not in tikr: non_tikr+=1; continue
    v,nome=tikr[k]
    if e_fondo(nome) or e_fondo(x.get("company")): fondi+=1; continue
    if v>=300: cand.append((x["ticker"],x["exchange"],nome[:36],v))
print("  non presenti nel TIKR attuale: %d  (esclusi a monte dalla fonte)" % non_tikr)
print("  riconosciuti come fondi/ETF:   %d" % fondi)
print("  CANDIDATI al rientro (>=300 MM USD, non fondi): %d" % len(cand))
print()
for t in sorted(cand,key=lambda x:-x[3]):
    print("   %-10s %-5s %-36s %8.0f MM" % t)
import json
open("/tmp/cand_nord.json","w").write(json.dumps(cand))
