import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_us_yahoo","order":"created_at.desc","limit":"1"}).json()
if r:
    print("eseguito:",r[0]["created_at"][:19])
    t=r[0]["log_text"]
    i=t.find("[Completamento seduta]")
    print(t[i:i+1400] if i>=0 else t[-1400:])
else: print("nessun log")
