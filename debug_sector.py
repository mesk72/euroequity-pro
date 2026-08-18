import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=120)
rd=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
tk={}
for row in rd:
    t=(row.get("Ticker") or "").strip()
    v=pn(row.get("Last Mkt Cap",""))
    if t and v: tk[t]=v
print("TIKR EU: %d titoli con capitalizzazione" % len(tk))
print()
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,mkt_cap","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break
print("=== confronto: nostro valore vs TIKR (mercati sospetti) ===")
n_ok=0;n_1000=0;n_altro=0;esempi=[]
for x in fu:
    if x["exchange"] not in ["OM","PA","MIL","XETRA","LSE","SWX","AT"]: continue
    v=x.get("mkt_cap")
    # TIKR usa il ticker con suffisso di borsa
    for cand in [x["ticker"], x["ticker"]+".ST", x["ticker"]+".PA", x["ticker"]+".MI"]:
        if cand in tk:
            t=tk[cand]
            if v is None: break
            rap=t/v if v else 0
            if 0.9<rap<1.1: n_ok+=1
            elif 900<rap<1100: 
                n_1000+=1
                if len(esempi)<10: esempi.append((x["ticker"],x["exchange"],v,t))
            else: n_altro+=1
            break
print("  corrispondono (stessa unita'):      %d" % n_ok)
print("  differenza di 1000x (miliardi!):    %d" % n_1000)
print("  altra differenza:                   %d" % n_altro)
print()
print("  esempi con fattore 1000:")
for t,e,nostro,tikr in esempi:
    print("    %-9s %-5s nostro=%.4f  TIKR=%.2f MM" % (t,e,nostro,tikr))
