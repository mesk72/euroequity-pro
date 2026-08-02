import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for nome in ["daily_eu_yahoo","daily_us_yahoo","daily_apac_yahoo"]:
    r=requests.get(U+"/rest/v1/script_logs",headers=H,
        params={"select":"created_at,log_text","script_name":"eq."+nome,
                "order":"created_at.desc","limit":"1"})
    d=r.json()
    print("=== %s ===" % nome)
    if not d: print("  nessun log"); continue
    print("  eseguito:", d[0]["created_at"])
    trovato=False
    for riga in d[0]["log_text"].split("\n"):
        if any(k in riga for k in ["Quintili","quintili","sector_quintile"]):
            print("  >>", riga.strip()); trovato=True
    if not trovato:
        print("  >> NESSUNA RIGA SUI QUINTILI NEL LOG")
        print("  ultime righe del log:")
        for riga in d[0]["log_text"].strip().split("\n")[-6:]:
            print("     ", riga.strip())
