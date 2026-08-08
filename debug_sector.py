import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for tk in ["EA","MDRX","SKYT","GAMI"]:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,in_universe,yahoo_ticker","ticker":"eq."+tk,"exchange":"eq.US"}).json()
    print(" ",tk,r)
