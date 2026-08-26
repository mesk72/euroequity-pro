import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for c in ["implied_growth","implied_growth_10y","ke","eps_ntm_dcf"]:
    r=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker",c:"not.is.null","limit":"1"})
    print("  %-20s su %s righe" % (c, r.headers.get("content-range","?").split("/")[-1]))
print()
d=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,implied_growth,implied_growth_10y,ke,eps_ntm_dcf",
            "ticker":"in.(NVDA,AAPL,MSFT,AVGO,LLY,TSLA)","exchange":"eq.US"}).json()
print("%-7s %11s %11s %8s %10s" % ("TITOLO","IMPLICITA","A 10 ANNI","Ke","EPS NTM"))
for x in sorted(d,key=lambda z:z["ticker"]):
    g=x.get("implied_growth"); g10=x.get("implied_growth_10y")
    print("%-7s %10s%% %10s%% %7s%% %10s" % (x["ticker"],
        ("%.1f"%(g*100)) if g is not None else "-",
        ("%.1f"%(g10*100)) if g10 is not None else "-",
        ("%.1f"%(x["ke"]*100)) if x.get("ke") is not None else "-",
        x.get("eps_ntm_dcf")))
