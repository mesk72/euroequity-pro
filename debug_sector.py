import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/macro_rates",headers=H,params={"select":"*","limit":"5"})
print("HTTP",r.status_code)
d=r.json()
if isinstance(d,list) and d:
    print("colonne:",list(d[0].keys()))
    for x in d: print("  ",x)
else: print(d)
