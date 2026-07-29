import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
             "Content-Type": "application/json"}
# Usa RPC per eseguire query raw se esiste una funzione, altrimenti verifica via information_schema con PostgREST
tables = ["institutional_viewers","latest_prices","script_logs","sector_aggregates","top500_universe"]
for t in tables:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{t}", headers={"apikey": SERVICE_KEY}, params={"select":"*","limit":"1"})
    print(f"{t}: HTTP {r.status_code} (anon key, senza auth) -> {'ESPOSTA' if r.status_code==200 else 'protetta'}")
