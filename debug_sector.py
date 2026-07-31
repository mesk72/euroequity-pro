import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_apac_yahoo",
            "order":"created_at.desc","limit":"1"})
d=r.json()
if d:
    print("Esecuzione:", d[0]["created_at"])
    for riga in d[0]["log_text"].split("\n"):
        if any(k in riga for k in ["BLOCCO SICUREZZA","Prezzi Yahoo","latest_prices","Riparazione","mai scritti"]):
            print("  "+riga.strip())
# controllo diretto: esiste una barra 31/07 per Tokyo?
print()
print("Barre datate 2026-07-31 gia' presenti per TSE:")
r2=requests.get(U+"/rest/v1/prices_eod",headers=H|{"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.TSE","date":"eq.2026-07-31","limit":"1"})
print("  ", r2.headers.get("content-range"))
