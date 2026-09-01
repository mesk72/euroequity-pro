import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== PDI.ASX: lo scalino e' sparito? ===")
d=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,adj_close","ticker":"eq.PDI","exchange":"eq.ASX",
            "date":"gte.2026-08-05","order":"date.asc"}).json()
prec=None
for x in d:
    v=x["adj_close"]
    var=("%+.1f%%"%((v/prec-1)*100)) if prec else ""
    print("   %s  %8.4f  %s" % (x["date"],v,var))
    prec=v
print()
print("=== cosa ha fatto il controllo split ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"}).json()
if r:
    t=r[0]["log_text"]; i=t.find("[Controllo split]")
    print(t[i:i+900] if i>=0 else "blocco non trovato nel log")
