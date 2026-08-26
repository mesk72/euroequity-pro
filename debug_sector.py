import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
rc=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","implied_growth":"not.is.null","limit":"1"})
print("titoli con crescita implicita:", rc.headers.get("content-range","?").split("/")[-1])
print()
d=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,implied_growth,implied_growth_10y,updated_at",
            "ticker":"in.(NVDA,AAPL,MSFT,AVGO,GOOGL,TSLA,META,AMZN,LLY)","exchange":"eq.US"}).json()
print("%-7s %10s %10s   %s" % ("TITOLO","IMPLICITA","A 10 ANNI","AGGIORNATO"))
for x in sorted(d,key=lambda z:z["ticker"]):
    ig=x.get("implied_growth"); i10=x.get("implied_growth_10y")
    print("%-7s %9s%% %9s%%   %s" % (x["ticker"],
        ("%.1f"%(ig*100)) if ig is not None else "-",
        ("%.1f"%(i10*100)) if i10 is not None else "-",
        str(x.get("updated_at"))[:16]))
