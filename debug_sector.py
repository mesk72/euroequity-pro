import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== tabella profiles: chi si e' registrato di recente ===")
r=requests.get(U+"/rest/v1/profiles",headers=H,
    params={"select":"*","order":"created_at.desc","limit":"5"})
d=r.json()
if isinstance(d,list) and d:
    print("colonne disponibili:", list(d[0].keys()))
    print()
    for x in d:
        print("  ", {k:v for k,v in x.items() if k in ("email","name","created_at","country","newsletter")})
else:
    print(d)
print()
print("=== esistono tabelle che registrano gli accessi? ===")
for t in ["auth_logs","sessions","user_sessions","access_log","page_views","analytics","login_log"]:
    rr=requests.get(U+"/rest/v1/"+t,headers=H,params={"select":"*","limit":"1"})
    if rr.status_code==200:
        print("  %-16s ESISTE" % t)
