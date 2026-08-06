import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== VISTA (quello che vede il sito) vs STORICO (la verita') ===")
for ex in ["TSE","SEHK","ASX","KRX","SGX","US","MIL","XETRA"]:
    # vista
    rows=[];off=0
    while True:
        rr=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=rr.json()
        if not isinstance(b,list) or not b: break
        rows+=b; off+=1000
        if len(b)<1000: break
    cv=Counter(x["price_date"] for x in rows)
    # storico
    rs=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    top_eod=rs[0]["date"] if rs else "-"
    top_mv=max(cv) if cv else "-"
    stato="ALLINEATA" if top_mv==top_eod else "INDIETRO"
    print("  %-6s vista=%s (%d titoli su quella data) | storico=%s -> %s" %
          (ex, top_mv, cv.get(top_mv,0), top_eod, stato))
