import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
r=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"wallet","limit":"1000"}).json()
from collections import Counter
print("  wallet in uso:", dict(Counter(x.get("wallet") for x in r)))
# prova a scrivere wallet 3
w=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","limit":"1"}).json()
if w:
    base=w[0]
    p={"user_id":base["user_id"],"ticker":"__W4TEST__","exchange":"US","company":"prova","wallet":3}
    rr=requests.post(U+"/rest/v1/watchlist?on_conflict=user_id,ticker,exchange,wallet",
        headers={**HP,"Prefer":"resolution=merge-duplicates,return=minimal"},json=[p])
    print("  scrittura wallet 3 -> HTTP", rr.status_code, rr.text[:120])
    requests.delete(U+"/rest/v1/watchlist",headers=H,params={"ticker":"eq.__W4TEST__"})
    print("  (riga di prova rimossa)")
