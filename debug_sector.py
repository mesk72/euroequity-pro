import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
v=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
    params={"select":"ticker,price,price_date","ticker":"eq.__CRONTEST__"}).json()
print("Esca nella vista:", v)
if v:
    print(">>> pg_cron FUNZIONA: la vista si e' aggiornata da sola.")
else:
    print(">>> non ancora assorbita.")
requests.delete(U+"/rest/v1/prices_eod",headers=H,params={"ticker":"eq.__CRONTEST__"})
print("(esca rimossa dallo storico)")
