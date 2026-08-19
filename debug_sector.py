import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None
SUF={".MI":"MIL",".DE":"XETRA",".PA":"PA",".AS":"AS",".MC":"MC",".BR":"BR",".LS":"LS",
     ".VI":"VI",".HE":"HE",".IR":"IR",".AT":"GR",".L":"LSE",".SW":"SWX",".ST":"OM",
     ".OL":"OB",".CO":"CPSE"}
tikr={}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
for row in csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))):
    t=(row.get("Ticker") or "").strip(); v=pn(row.get("Last Mkt Cap",""))
    if not t or not v: continue
    for suf,ex in SUF.items():
        if t.endswith(suf): tikr[(t[:-len(suf)],ex)]=v; break

print("=== i titoli con valore assurdo: sono in TIKR? ===")
for tk,ex in [("NEOBO","OM"),("NIVI B","OM"),("FLEXO","GR"),("QUEST","GR"),("DATA","MIL"),("GE","MIL")]:
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"mkt_cap","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    nostro=f[0].get("mkt_cap") if f else None
    in_tikr=tikr.get((tk,ex))
    print("  %-8s %-5s nostro=%-10s TIKR=%s" % (tk,ex,nostro,in_tikr if in_tikr else "NON PRESENTE"))
print()
print("=== quanti titoli con mkt_cap<1 sono ASSENTI da TIKR? ===")
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,mkt_cap","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break
piccoli=[x for x in fu if x.get("mkt_cap") is not None and x["mkt_cap"]<1]
in_t=sum(1 for x in piccoli if (x["ticker"],x["exchange"]) in tikr)
print("  titoli con mkt_cap<1: %d" % len(piccoli))
print("  di cui presenti in TIKR: %d" % in_t)
print("  di cui ASSENTI da TIKR:  %d" % (len(piccoli)-in_t))
