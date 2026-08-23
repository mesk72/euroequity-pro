import os, requests, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== quante righe US ci sono davvero nella vista? ===")
r=requests.get(U+"/rest/v1/latest_prices_mv",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","limit":"1"})
print("  conteggio server:", r.headers.get("content-range","?").split("/")[-1])
print()
print("=== lettura paginata, pagina per pagina ===")
tot=0; off=0
while True:
    t0=time.time()
    rr=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"ticker,price_date","exchange":"eq.US","limit":"1000","offset":str(off)},timeout=120)
    if rr.status_code!=200:
        print("  offset %5d -> HTTP %s  %s" % (off,rr.status_code,rr.text[:120])); break
    b=rr.json()
    if not isinstance(b,list):
        print("  offset %5d -> risposta anomala: %s" % (off,str(b)[:150])); break
    print("  offset %5d -> %4d righe  (%.1fs)" % (off,len(b),time.time()-t0))
    tot+=len(b); off+=1000
    if len(b)<1000: break
print("  TOTALE letto:",tot)
print()
print("=== distribuzione date US nella vista ===")
from collections import Counter
d=[];off=0
while True:
    b=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price_date","exchange":"eq.US","limit":"1000","offset":str(off)},timeout=120).json()
    if not isinstance(b,list) or not b: break
    d+=[x["price_date"] for x in b]; off+=1000
    if len(b)<1000: break
c=Counter(d)
for k,v in sorted(c.items(),reverse=True)[:5]: print("   %s : %d" % (k,v))
print()
print("=== quanti titoli US in universo hanno una riga nella vista? ===")
uni=set();off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(off)}).json()
    if not isinstance(b,list) or not b: break
    uni.update(x["ticker"] for x in b); off+=1000
    if len(b)<1000: break
inview=set();off=0
while True:
    b=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"ticker","exchange":"eq.US","limit":"1000","offset":str(off)}).json()
    if not isinstance(b,list) or not b: break
    inview.update(x["ticker"] for x in b); off+=1000
    if len(b)<1000: break
print("  universo US: %d | nella vista: %d | SENZA riga: %d" % (len(uni),len(inview),len(uni-inview)))
print("  esempi senza riga:", sorted(uni-inview)[:12])
