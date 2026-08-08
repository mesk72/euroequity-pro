import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","limit":"5"})
d=r.json()
print("colonne:", list(d[0].keys()) if isinstance(d,list) and d else d)
print()
r2=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","ticker":"eq.LLY"})
print("righe per LLY:", r2.json())
print()
rc=requests.get(U+"/rest/v1/watchlist",headers={**H,"Prefer":"count=exact"},params={"select":"id","limit":"1"})
print("righe totali watchlist:", rc.headers.get("content-range","?").split("/")[-1])
