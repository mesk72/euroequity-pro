import os, requests, yfinance as yf, pandas as pd
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for nome in ["Neobo","NIVI"]:
    print("=== cerco %s ===" % nome)
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,yahoo_ticker,in_universe,sector","company":"ilike.*%s*"%nome}).json()
    if not r:
        r=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,exchange,company,yahoo_ticker,in_universe,sector","ticker":"ilike.*%s*"%nome}).json()
    for x in r: print("  ",x)
    for x in r:
        tk,ex=x["ticker"],x["exchange"]
        rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
            params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"limit":"1"})
        n=rc.headers.get("content-range","?").split("/")[-1]
        f=requests.get(U+"/rest/v1/fundamentals",headers=H,
            params={"select":"value_score,growth_score,combined_rank,eps_growth,rev_growth,mom6m,mom12m,pe_trailing,pb,mkt_cap",
                    "ticker":"eq."+tk,"exchange":"eq."+ex}).json()
        mv=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price,price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
        print("    storico: %s righe | vista: %s" % (n, mv))
        print("    fondamentali:", f)
        yt=x.get("yahoo_ticker") or tk
        try:
            df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            print("    yahoo %s: %s" % (yt,[(i.strftime("%d/%m"),round(float(v),2)) for i,v in list(cl.items())[-3:]]))
        except Exception as e:
            print("    yahoo errore",str(e)[:40])
    print()
