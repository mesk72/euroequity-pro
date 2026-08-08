import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
base=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"*","ticker":"eq.LLY"}).json()[0]
print("LLY prima:", [(x["wallet"]) for x in requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"wallet","ticker":"eq.LLY"}).json()])

print()
print("PROVA 1: stesso titolo in un wallet DIVERSO (deve riuscire)")
p={"user_id":base["user_id"],"ticker":"LLY","exchange":"US","company":base["company"],
   "combined_rank":base["combined_rank"],"wallet":3}
w=requests.post(U+"/rest/v1/watchlist",headers=HP,json=[p])
print("  wallet 3 -> HTTP",w.status_code, "OK" if w.status_code in (200,201) else w.text[:150])

print()
print("PROVA 2: stesso titolo nello STESSO wallet (deve essere rifiutato)")
w2=requests.post(U+"/rest/v1/watchlist",headers=HP,json=[p])
print("  wallet 3 di nuovo -> HTTP",w2.status_code, "correttamente rifiutato" if w2.status_code==409 else "ATTENZIONE: duplicato permesso!")

print()
righe=requests.get(U+"/rest/v1/watchlist",headers=H,params={"select":"id,wallet","ticker":"eq.LLY"}).json()
print("LLY adesso nei wallet:", sorted(x["wallet"] for x in righe))
# rimuovo la riga di prova
for x in righe:
    if x["wallet"]==3:
        requests.delete(U+"/rest/v1/watchlist",headers=H,params={"id":"eq."+x["id"]})
        print("(riga di prova rimossa: aggiungilo tu dal sito)")
        break
