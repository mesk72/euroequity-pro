import os, requests, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== lettura di stocks per US, pagina per pagina ===")
SEL="ticker,company,sector,country,in_universe"
off=0; tot=0
while True:
    t0=time.time()
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":SEL,"exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=120)
    if r.status_code!=200:
        print("  offset %5d -> HTTP %s  %s" % (off,r.status_code,r.text[:150])); break
    b=r.json()
    if not isinstance(b,list): print("  offset %5d risposta anomala" % off); break
    print("  offset %5d -> %4d righe (%.1fs)" % (off,len(b),time.time()-t0))
    tot+=len(b)
    if not b: break
    off+=len(b)
    if off>20000: break
print("  TOTALE:",tot)
print()
print("=== e con la selezione completa che usa il rapporto? ===")
SEL2="ticker,company,sector,country,in_universe,yahoo_ticker"
off=0; tot2=0
while True:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":SEL2,"exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=120)
    b=r.json()
    if not isinstance(b,list) or not b: break
    tot2+=len(b); off+=len(b)
print("  TOTALE:",tot2)
