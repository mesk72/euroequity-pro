import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","div_yield":"not.is.null","limit":"1"})
tot=requests.get(U+"/rest/v1/fundamentals",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","limit":"1"})
print("righe con div_yield valorizzato:", r.headers.get("content-range","?").split("/")[-1])
print("righe totali fundamentals    :", tot.headers.get("content-range","?").split("/")[-1])
print()
d=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,exchange,div_yield","div_yield":"not.is.null","limit":"8"}).json()
print("esempi:",d)
