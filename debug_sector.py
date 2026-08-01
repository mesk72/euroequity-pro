import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
SVC=os.environ.get("SUPABASE_SERVICE_KEY","")

print("Con chiave di servizio (quella che uso io):")
r=requests.get(U+"/rest/v1/news_cache",headers={"apikey":SVC,"Authorization":"Bearer "+SVC,"Prefer":"count=exact"},
    params={"select":"ticker","limit":"1"})
print("  HTTP",r.status_code," righe:",r.headers.get("content-range","?").split("/")[-1])

# la chiave pubblica usata dal sito e' nelle variabili d'ambiente del progetto,
# qui non l'abbiamo: verifichiamo invece se la tabella ha RLS attiva
print("\nAltre tabelle lette dal sito senza problemi, per confronto:")
for t in ["stocks","latest_prices","sector_quintile_partials","news_cache"]:
    r=requests.get(U+"/rest/v1/"+t,headers={"apikey":SVC,"Authorization":"Bearer "+SVC,"Prefer":"count=exact"},
        params={"select":"*","limit":"1"})
    print("  %-26s HTTP %s righe %s" % (t,r.status_code,r.headers.get("content-range","?").split("/")[-1]))
