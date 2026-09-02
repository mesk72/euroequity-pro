import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== UIBU in anagrafica ===")
r=requests.get(U+"/rest/v1/stocks",headers=H,params={"select":"*","ticker":"eq.UIBU"}).json()
for x in r:
    print("  ", {k:v for k,v in x.items() if k in ("ticker","exchange","company","sector","country","in_universe","yahoo_ticker")})
print()
for x in r:
    ex=x["exchange"]
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"mkt_cap,value_score,growth_score","ticker":"eq.UIBU","exchange":"eq."+ex}).json()
    print("  fondamentali:",f)
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq.UIBU","exchange":"eq."+ex,"limit":"1"})
    print("  righe di prezzo:", rc.headers.get("content-range","?").split("/")[-1])
print()
print("=== altri titoli con settore numerico (71-77) ===")
o=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,sector","in_universe":"eq.true","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    o+=b; off+=len(b)
strani=[x for x in o if (x.get("sector") or "").strip().isdigit()]
print("  quanti:",len(strani))
for x in strani[:20]: print("   %-10s %-5s settore=%-4s %s" % (x["ticker"],x["exchange"],x.get("sector"),(x.get("company") or "")[:34]))
