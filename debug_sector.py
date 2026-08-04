import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== ASML.AS — le tre fonti a confronto ===")
r1=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date,adj_close","ticker":"eq.ASML","exchange":"eq.AS","order":"date.desc","limit":"5"}).json()
print("\n1) prices_eod  (lo legge il GRAFICO):")
for x in r1: print("     %s  %.2f" % (x["date"],x["adj_close"]))
r2=requests.get(U+"/rest/v1/latest_prices",headers=H,
    params={"select":"price,prev_price,price_date,change1d","ticker":"eq.ASML","exchange":"eq.AS"}).json()
print("\n2) latest_prices  (lo leggono SCREENER e TABELLA):")
print("    ",r2)
r3=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"price,change1d,mom1w,mom1m,mom6m,mom12m","ticker":"eq.ASML","exchange":"eq.AS"}).json()
print("\n3) fundamentals  (contiene un'ALTRA copia del prezzo + i momentum):")
print("    ",r3)
r4=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"price,last_price_date","ticker":"eq.ASML","exchange":"eq.AS"}).json()
print("\n4) stocks  (contiene una QUARTA copia del prezzo):")
print("    ",r4)
