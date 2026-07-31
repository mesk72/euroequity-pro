import os, requests
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]

# distribuzione in CACHE (quello che vede il sito)
tutte=[]
for ex in EU:
    off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        tutte+=[x["price_date"] for x in b]; off+=1000
        if len(b)<1000: break
c=Counter(tutte)
print("EUROPA - distribuzione in cache (%d titoli):" % len(tutte))
for d,n in sorted(c.items(), reverse=True)[:6]:
    print("   %s  %5d titoli" % (d,n))

# righe grezze residue al 30/07
tot30=0
for ex in EU:
    r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq.2026-07-30","limit":"1"})
    tot30+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("\nRighe grezze europee al 30/07 rimaste: %d  (attese: 0)" % tot30)

# incoerenze grezzo/cache su un campione ampio
print("\nControllo coerenza grezzo/cache su 40 titoli a campione:")
disallineati=0; controllati=0
for ex in ["HE","OM","CPSE","SWX","XETRA"]:
    r=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"ticker,price_date","exchange":"eq."+ex,"limit":"8"})
    for x in r.json():
        g=requests.get(U+"/rest/v1/prices_eod",headers=H,
            params={"select":"date","ticker":"eq."+x["ticker"],"exchange":"eq."+ex,
                    "order":"date.desc","limit":"1"}).json()
        controllati+=1
        if not g or g[0]["date"]!=x["price_date"]:
            disallineati+=1
            print("   DISALLINEATO %s.%s cache=%s grezzo=%s" % (x["ticker"],ex,x["price_date"], g[0]["date"] if g else "-"))
print("   controllati %d, disallineati %d" % (controllati,disallineati))
