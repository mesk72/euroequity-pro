import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Confronto STORICO (la verita') vs VISTA (cio' che legge il sito)")
print()
for tk,ex in [("EA","US"),("MDRX","US"),("SKYT","US"),("MAN","VI"),("SIC","SWX"),("SEC","TSX")]:
    e=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    v=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("  %-6s.%-4s storico=%s | vista=%s" % (tk,ex,
        (e[0]["date"],e[0]["adj_close"]) if e else "-",
        v[0]["price_date"] if v else "-"))
print()
r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","date":"eq.2026-08-07","limit":"1"})
print("Righe totali datate 7/8 nello storico:", r.headers.get("content-range","?").split("/")[-1])
