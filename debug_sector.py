import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K,"Prefer":"count=exact"}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
tot=0
print("Righe datate 2026-07-30 in prices_eod, per mercato europeo:")
for ex in EU:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq.2026-07-30","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1])
    tot+=n
    if n: print("  %-6s %4d" % (ex,n))
print("  TOTALE %d" % tot)
