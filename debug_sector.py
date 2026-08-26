import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== i dati che servono al modello sono aggiornati? ===")
r=requests.get(U+"/rest/v1/macro_rates",headers=H,params={"select":"*","order":"date.desc","limit":"3"}).json()
print("  macro_rates (tasso Treasury):")
for x in (r if isinstance(r,list) else [r]): print("   ",x)
rc=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","beta":"not.is.null","exchange":"eq.US","limit":"1"})
print("  titoli USA con beta:", rc.headers.get("content-range","?").split("/")[-1])
rc2=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","limit":"1"})
print("  titoli USA totali:", rc2.headers.get("content-range","?").split("/")[-1])
