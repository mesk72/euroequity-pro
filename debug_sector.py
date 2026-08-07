import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.sorvegliante","order":"created_at.desc","limit":"5"}).json()
if not r:
    print("Nessun intervento registrato: significa che il sorvegliante ha")
    print("controllato e ha trovato tutto regolare (scrive solo quando agisce).")
else:
    for x in r: print(x["created_at"][:19], "|", x["log_text"])
