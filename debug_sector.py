import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
r=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","ticker":"eq.LLY"}).json()
base=r[0]
prova={"user_id":base["user_id"],"ticker":"LLY","exchange":"US",
       "company":base["company"],"combined_rank":base["combined_rank"],"wallet":3}
w=requests.post(U+"/rest/v1/watchlist",headers=HP,json=[prova])
print("inserimento in wallet 3 -> HTTP",w.status_code)
print(w.text[:400])
# pulizia se e' andato a buon fine
d=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"id,wallet","ticker":"eq.LLY"}).json()
print("righe LLY ora:",d)
for x in d:
    if x["wallet"]==3:
        requests.delete(U+"/rest/v1/watchlist",headers=H,params={"id":"eq."+x["id"]})
        print("(riga di prova rimossa)")
