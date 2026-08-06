import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"})
d=r.json()
print("APAC eseguito:", d[0]["created_at"][:19])
print()
for riga in d[0]["log_text"].split("\n"):
    if any(k in riga for k in ["SEHK","TSE","Verifica seduta","recuperati","nessun recupero","BLOCCO","Prezzi Yahoo","vista"]):
        print("  ",riga.strip()[:130])
print()
print("=== stato ATTUALE per exchange asiatici ===")
for ex in ["TSE","SEHK","KRX","SGX","ASX"]:
    rows=[]; off=0
    while True:
        rr=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=rr.json()
        if not isinstance(b,list) or not b: break
        rows+=b; off+=1000
        if len(b)<1000: break
    c=Counter(x["price_date"] for x in rows)
    print("  %-5s %s" % (ex,dict(sorted(c.items(),reverse=True)[:3])))
