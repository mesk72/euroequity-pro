import os, requests, yfinance as yf, pandas as pd
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

# titoli nordici che nel NOSTRO db risultano al 30/07
sospetti=[]
for ex,suf in [("OM",".ST"),("HE",".HE"),("CPSE",".CO")]:
    r=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"ticker","exchange":"eq."+ex,"price_date":"eq.2026-07-30","limit":"3"})
    for x in r.json(): sospetti.append((x["ticker"],ex,suf))

print("=== Titoli che nel NOSTRO db hanno il 30/07: Yahoo ce l'ha davvero? ===")
for tk,ex,suf in sospetti:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,
                "order":"date.desc","limit":"3"})
    nostro=[(x["date"],x["adj_close"]) for x in r.json()]
    ytk=tk+suf
    try:
        df=yf.download(ytk,period="6d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        yahoo=[(cl.index[i].strftime("%Y-%m-%d"), round(float(cl.iloc[i]),2))
               for i in range(max(0,len(cl)-3),len(cl))]
    except Exception as e:
        yahoo="errore: "+str(e)[:40]
    print("\n  %s.%s (%s)" % (tk,ex,ytk))
    print("    nostro db: %s" % nostro)
    print("    yahoo ora: %s" % yahoo)

print()
print("=== prices_eod ha una colonna con l'ora di scrittura? ===")
r=requests.get(U+"/rest/v1/prices_eod",headers=H,params={"select":"*","limit":"1"})
d=r.json()
print("  colonne:", list(d[0].keys()) if isinstance(d,list) and d else "?")
