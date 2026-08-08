import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_us_yahoo","order":"created_at.desc","limit":"1"}).json()
print("eseguito:",r[0]["created_at"][:19])
print()
txt=r[0]["log_text"]
inizio=txt.find("[Completamento seduta]")
if inizio<0:
    print(">>> LA FASE DI COMPLETAMENTO NON COMPARE NEL LOG <<<")
    print("ultime 20 righe:")
    for riga in txt.strip().split("\n")[-20:]: print("  ",riga.strip()[:120])
else:
    print("--- dalla fase di completamento in poi ---")
    for riga in txt[inizio:].split("\n")[:30]: print("  ",riga.strip()[:125])
