import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]

print("=== 1. DATA PREVALENTE per singolo exchange europeo (latest_prices) ===")
for ex in EU:
    rows=[]; off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        rows+=b; off+=1000
        if len(b)<1000: break
    c=Counter(x["price_date"] for x in rows)
    print("  %-6s n=%4d  %s" % (ex,len(rows),dict(c.most_common(3))))

print()
print("=== 2. DATI GREZZI prices_eod vs CACHE latest_prices (titoli campione) ===")
for tk,ex in [("ASML","AS"),("SAP","XETRA"),("MC","PA"),("NESN","SWX"),("SHEL","LSE"),("ISP","MIL")]:
    r1=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"})
    r2=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"price_date","ticker":"eq."+tk,"exchange":"eq."+ex})
    g=r1.json(); c=r2.json()
    print("  %-6s.%-6s  grezzo=%s   cache=%s" % (
        tk,ex,
        g[0]["date"] if isinstance(g,list) and g else "-",
        c[0]["price_date"] if isinstance(c,list) and c else "-"))

print()
print("=== 3. ULTIMA DATA in prices_eod per exchange europeo ===")
for ex in EU:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","exchange":"eq."+ex,"order":"date.desc","limit":"1"})
    d=r.json()
    print("  %-6s  %s" % (ex, d[0]["date"] if isinstance(d,list) and d else "-"))
