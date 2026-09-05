import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
print("=== stesso titolo in piu' wallet: il vincolo lo permette ancora? ===")
b=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","limit":"1"}).json()[0]
uid=b["user_id"]
esiti=[]
for w in [2,3]:
    p={"user_id":uid,"ticker":"__MULTI__","exchange":"US","company":"prova","wallet":w}
    r=requests.post(U+"/rest/v1/watchlist",headers={**HP,"Prefer":"return=minimal"},json=[p])
    esiti.append((w,r.status_code,r.text[:90]))
for w,c,t in esiti: print("   wallet %d -> HTTP %s %s" % (w,c,t))
d=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"wallet","ticker":"eq.__MULTI__"}).json()
print("   righe create:", [x["wallet"] for x in d])
requests.delete(U+"/rest/v1/watchlist",headers=H,params={"ticker":"eq.__MULTI__"})
print("   (pulito)")
