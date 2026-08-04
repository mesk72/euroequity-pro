import os, requests
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

print("=== 1. Ultimo log EU: ci sono errori di scrittura? ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_eu_yahoo","order":"created_at.desc","limit":"1"})
d=r.json()
if d:
    print("eseguito:",d[0]["created_at"])
    for riga in d[0]["log_text"].split("\n"):
        if any(k in riga for k in ["ERRORE","Prezzi Yahoo","BLOCCO","Data piu' recente nel mercato AS","Data piu' recente nel mercato MIL"]):
            print("  ",riga.strip())

print()
print("=== 2. Quante righe al 3/8 esistono per mercato europeo? ===")
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
tot=0
for ex in EU:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq.2026-08-03","limit":"1"})
    n=int(rc.headers.get("content-range","0/0").split("/")[-1]); tot+=n
    if n: print("  %-6s %4d" % (ex,n))
print("  TOTALE al 3/8: %d" % tot)

print()
print("=== 3. PROVA DI SCRITTURA con la chiave attuale ===")
test={"ticker":"__WTEST__","exchange":"AS","date":"2026-08-03","adj_close":1.23}
w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=[test])
print("  POST -> HTTP",w.status_code, w.text[:200])
chk=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"ticker,date","ticker":"eq.__WTEST__"}).json()
print("  riga presente dopo scrittura:", chk)
requests.delete(U+"/rest/v1/prices_eod",headers=H,params={"ticker":"eq.__WTEST__"})
print("  (pulita)")

print()
print("=== 4. Scrittura di un ticker VERO mancante (ASML 3/8) ===")
real={"ticker":"ASML","exchange":"AS","date":"2026-08-03","adj_close":1419.60}
w2=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=[real])
print("  POST -> HTTP",w2.status_code)
chk2=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,adj_close","ticker":"eq.ASML","exchange":"eq.AS","order":"date.desc","limit":"3"}).json()
print("  ASML ora:",chk2)
