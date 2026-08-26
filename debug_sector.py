import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},params={"select":"ticker","limit":"1"})
print("righe totali fundamentals:", r.headers.get("content-range","?").split("/")[-1])
d=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,exchange,implied_growth_10y,updated_at","ticker":"eq.NVDA","exchange":"eq.US"}).json()
print("righe per NVDA.US:", len(d))
for x in d: print("  ",x)
