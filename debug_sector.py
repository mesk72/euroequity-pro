import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Titoli che avevo recuperato stamattina — cosa c'e' ADESSO nel database?")
print()
for tk,ex in [("TYA","MIL"),("YRM","MIL"),("RWY","MIL"),("MALT","PA"),("CDU","LS"),("HED","VI")]:
    eod=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"3"}).json()
    mv=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("  %-7s.%-4s storico: %s" % (tk,ex,[(x["date"],x["adj_close"]) for x in eod] if eod else "-"))
    print("               vista  : %s" % (mv[0]["price_date"] if mv else "-"))
print()
print("=== la vista si sta aggiornando? ===")
r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.MIL","date":"eq.2026-08-17","limit":"1"})
print("  righe MIL al 17/08 nello storico:", r.headers.get("content-range","?").split("/")[-1])
r2=requests.get(U+"/rest/v1/latest_prices_mv",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.MIL","price_date":"eq.2026-08-17","limit":"1"})
print("  righe MIL al 17/08 nella vista:", r2.headers.get("content-range","?").split("/")[-1])
