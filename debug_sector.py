import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_report",
            "order":"created_at.desc","limit":"3"})
d=r.json()
if not d: print("nessun esito registrato")
for x in d: print(x["created_at"], "|", x["log_text"])
