import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
# elenco tabelle e stato RLS non e' leggibile via REST: provo l'accesso ANONIMO
# usando la chiave pubblica del sito, che e' quella che un attaccante avrebbe.
print("=== TEST DI ACCESSO ANONIMO (senza chiave) ===")
for t in ["stocks","fundamentals","prices_eod","latest_prices","profiles","watchlist",
          "portfolios","institutional_viewers","script_logs","daily_log",
          "sector_quintile_partials","top500_universe","report_requests","news_cache"]:
    try:
        r=requests.get(U+"/rest/v1/"+t,params={"select":"*","limit":"1"},timeout=20)
        print("  %-26s HTTP %s %s" % (t, r.status_code, "<-- LEGGIBILE SENZA CHIAVE" if r.status_code==200 else ""))
    except Exception as e:
        print("  %-26s errore %s" % (t,str(e)[:40]))
