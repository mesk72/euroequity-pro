import os, requests, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

print("PROVA: scrivo un prezzo finto nello storico e verifico che la vista")
print("lo assorba da sola entro 10 minuti, senza che nessuno intervenga.")
print()
esca={"ticker":"__CRONTEST__","exchange":"SGX","date":"2026-08-05","adj_close":42.42}
requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=[esca])
c=requests.get(U+"/rest/v1/prices_eod",headers=H,params={"select":"ticker","ticker":"eq.__CRONTEST__"}).json()
print("  scritto nello storico:", len(c)==1)
v=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,params={"select":"ticker","ticker":"eq.__CRONTEST__"}).json()
print("  presente nella vista ADESSO:", len(v)==1, "(atteso: no, deve arrivare col prossimo ricalcolo)")
print()
print("  Lascio l'esca. Ricontrollo fra qualche minuto.")
print()
print("=== stato generale della vista ===")
tot=0; c2=Counter()
for ex in ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]:
    off=0
    while True:
        rr=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=rr.json()
        if not isinstance(b,list) or not b: break
        for x in b: c2[x["price_date"]]+=1; tot+=1
        off+=1000
        if len(b)<1000: break
print("  titoli nella vista: %d" % tot)
for d,n in sorted(c2.items(),reverse=True)[:4]:
    print("    %s : %5d (%.1f%%)" % (d,n,n/tot*100))
