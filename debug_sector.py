import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.fondamentali_auto","order":"created_at.desc","limit":"5"}).json()
if not r: print("nessuna traccia registrata")
for x in r: print(x["created_at"][:19],"|",x["log_text"][:200])
