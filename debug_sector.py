import requests, os
print("=== endpoint nuovi ===")
for n,u in [("rapporto","https://forwardalpha.pro/api/cron/trigger-report"),
            ("Europa sera","https://forwardalpha.pro/api/cron/trigger-daily-eu")]:
    try:
        r=requests.get(u,timeout=60); print("  %-12s HTTP %s  %s" % (n,r.status_code,r.text[:110]))
    except Exception as e: print("  %-12s errore %s" % (n,str(e)[:50]))

print()
print("=== esito fase di verifica negli script appena girati ===")
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for nome in ["daily_apac_yahoo","daily_us_yahoo","daily_eu_yahoo"]:
    r=requests.get(U+"/rest/v1/script_logs",headers=H,
        params={"select":"created_at,log_text","script_name":"eq."+nome,"order":"created_at.desc","limit":"1"})
    d=r.json()
    print("--- %s ---" % nome)
    if not d: print("   nessun log"); continue
    print("   eseguito:",d[0]["created_at"][:19])
    for riga in d[0]["log_text"].split("\n"):
        if any(k in riga for k in ["Verifica seduta","recuperati","nessun recupero","vista aggiornata","ERRORE","Prezzi Yahoo"]):
            print("    ",riga.strip()[:115])
