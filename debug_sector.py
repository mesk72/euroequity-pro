import requests, os
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
HS={"apikey":SK,"Authorization":"Bearer "+SK}
# 1) il dato ESISTE nel database?
r=requests.get(BASE+"/rest/v1/prices_eod",headers=HS,
    params={"select":"date,adj_close","ticker":"eq.AAPL","exchange":"eq.US","order":"date.desc","limit":"3"},timeout=30)
print("storico AAPL nel database:", r.json())
# 2) l'API senza login risponde vuota per PROTEZIONE (comportamento voluto dal 20/7)?
r2=requests.get("https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=400",timeout=60)
print()
print("API senza login -> HTTP %s, corpo: %s" % (r2.status_code, r2.text[:150]))
print()
print("Se il database ha i dati e l'API vuota risponde 200 con lista vuota,")
print("il comportamento e' quello previsto: lo storico e' riservato ai registrati.")
