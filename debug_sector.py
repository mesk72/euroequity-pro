import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== Storico completo per titolo (quello che usa il GRAFICO) ===")
for tk,ex in [("ASML","AS"),("SAP","XETRA"),("AAPL","US"),("7203","TSE"),("BHP","ASX")]:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"limit":"1"})
    n=rc.headers.get("content-range","0/0").split("/")[-1]
    prima=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.asc","limit":"1"}).json()
    ultima=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    print("  %-6s.%-5s %5s sedute  dal %s al %s" % (tk,ex,n,
        prima[0]["date"] if prima else "-", ultima[0]["date"] if ultima else "-"))

print()
print("=== Cosa restituisce l'API del grafico (5 anni) ===")
for tk,ex in [("AAPL","US"),("ASML","AS")]:
    try:
        r=requests.get("https://forwardalpha.pro/api/db/history?ticker=%s&exchange=%s&days=1825"%(tk,ex),timeout=60)
        d=r.json()
        h=d.get("history",[])
        m=d.get("momentum",{})
        print("  %-6s.%-4s punti=%d  dal %s al %s  | mom12m=%s mom5y=%s" % (tk,ex,len(h),
            h[0]["date"] if h else "-", h[-1]["date"] if h else "-", m.get("mom12m"), m.get("mom5y")))
    except Exception as e:
        print("  %s errore %s" % (tk,str(e)[:60]))
