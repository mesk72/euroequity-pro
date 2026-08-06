import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"})
d=r.json()
print("APAC eseguito:", d[0]["created_at"][:19])
print()
for riga in d[0]["log_text"].split("\n"):
    if any(k in riga for k in ["Completamento seduta","passata","nessun progresso","Prezzi Yahoo"]):
        print("  ",riga.strip()[:135])
