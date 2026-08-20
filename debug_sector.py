import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
nuovi=[("MAERSK B","CPSE"),("NSIS B","CPSE"),("CARL B","CPSE"),("COLO B","CPSE"),
       ("ROCK B","CPSE"),("ALK B","CPSE"),("GSF","OB"),("PEN","OB"),("AKAST","OB")]
print("=== i 28 reintegrati hanno i fondamentali? ===")
print("%-10s %-5s %-9s %-9s %-9s %-9s %-7s %-7s" % ("TICKER","EX","PE_TRAIL","PE_FWD","PB","EPS_GR","VALUE","GROWTH"))
for tk,ex in nuovi:
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"pe_trailing,pe_forward,pb,eps_growth,rev_growth,value_score,growth_score,combined_rank",
                "ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    if not f:
        print("%-10s %-5s  NESSUNA RIGA IN FUNDAMENTALS" % (tk,ex)); continue
    x=f[0]
    print("%-10s %-5s %-9s %-9s %-9s %-9s %-7s %-7s" % (tk,ex,
        x.get("pe_trailing"),x.get("pe_forward"),x.get("pb"),x.get("eps_growth"),
        x.get("value_score"),x.get("growth_score")))
print()
print("=== quanti dei 28 hanno una riga in fundamentals? ===")
rc=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"in.(CPSE,OB)","limit":"1"})
print("  righe fundamentals per CPSE+OB:", rc.headers.get("content-range","?").split("/")[-1])
rc2=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"in.(CPSE,OB)","in_universe":"eq.true","limit":"1"})
print("  titoli in universo CPSE+OB:", rc2.headers.get("content-range","?").split("/")[-1])
print()
print("=== dove si calcola combined_rank? ===")
