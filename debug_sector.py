import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== NSKOG e' nella tua watchlist? ===")
r=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","ticker":"eq.NSKOG"}).json()
for x in r: print("  ",x)
print()
print("=== aveva prezzi PRIMA di oggi? (le righe che ho scritto io sono di oggi) ===")
rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
    params={"select":"date","ticker":"eq.NSKOG","exchange":"eq.OB","limit":"1"})
print("  righe totali ora:", rc.headers.get("content-range","?").split("/")[-1])
r2=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,scritto_il","ticker":"eq.NSKOG","exchange":"eq.OB","order":"date.desc","limit":"5"}).json()
print("  ultime righe con data di scrittura:")
for x in r2: print("   ",x)
print()
print("=== quando e' stata scritta la PIU' VECCHIA riga? ===")
r3=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,scritto_il","ticker":"eq.NSKOG","exchange":"eq.OB","order":"scritto_il.asc","limit":"3"}).json()
for x in r3: print("   ",x)
print()
print("=== altri titoli OB: quanti sono in universo? ===")
for v in ["true","false"]:
    rc=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq.OB","in_universe":"eq."+v,"limit":"1"})
    print("  in_universe=%s: %s" % (v, rc.headers.get("content-range","?").split("/")[-1]))
