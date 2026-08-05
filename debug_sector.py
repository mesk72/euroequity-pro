import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== LOG della fase di verifica ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_eu_yahoo","order":"created_at.desc","limit":"1"})
d=r.json()
if d:
    print("eseguito:",d[0]["created_at"])
    dentro=False
    for riga in d[0]["log_text"].split("\n"):
        if "[2b/5]" in riga: dentro=True
        if dentro: print("  ",riga.strip())
        if "Verifica seduta:" in riga: dentro=False
    for riga in d[0]["log_text"].split("\n"):
        if any(k in riga for k in ["Prezzi Yahoo","vista aggiornata","BLOCCO SICUREZZA"]):
            print("  >>",riga.strip())
print()
print("=== EUROPA: distribuzione date nella vista ===")
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
c=Counter()
for ex in EU:
    off=0
    while True:
        b=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)}).json()
        if not isinstance(b,list) or not b: break
        for x in b: c[x["price_date"]]+=1
        off+=1000
        if len(b)<1000: break
for k,v in sorted(c.items(),reverse=True)[:5]:
    print("   %s : %5d titoli" % (k,v))
