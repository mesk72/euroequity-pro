import os, requests
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
HS={"apikey":SK,"Authorization":"Bearer "+SK}
# 1) i dati ci sono ancora nel database?
r=requests.get(BASE+"/rest/v1/prices_eod",headers=HS,
    params={"select":"date,adj_close","ticker":"eq.AAPL","exchange":"eq.US","order":"date.desc","limit":"3"},timeout=30)
print("dati grezzi AAPL (chiave servizio):", r.status_code, r.text[:150])
# 2) l'API del sito senza login
r2=requests.get("https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=400",timeout=60)
print()
print("API grafico senza login:", r2.status_code, r2.text[:200])
