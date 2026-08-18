import os, requests, yfinance as yf, pandas as pd
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== cerco NSKOG nella tabella stocks ===")
for f in ["ticker=ilike.*NSKOG*","company=ilike.*Norske Skog*","ticker=eq.NSKOG"]:
    k,v=f.split("=",1)
    r=requests.get(U+"/rest/v1/stocks",headers=H,params={"select":"ticker,exchange,company,yahoo_ticker,in_universe",k:v})
    d=r.json()
    if isinstance(d,list) and d:
        for x in d: print("  ",x)
        break
print()
print("=== quante righe di storico ha? ===")
for tk,ex in [("NSKOG","OB")]:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"limit":"1"})
    print("  righe in prices_eod:", rc.headers.get("content-range","?").split("/")[-1])
    mv=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price,price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("  nella vista:", mv)
print()
print("=== cosa ha Yahoo? ===")
for yt in ["NSKOG.OL","NSKOG.OB"]:
    try:
        df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
        if df.empty: print("  %-10s VUOTO" % yt); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        print("  %-10s %s" % (yt,[(i.strftime("%d/%m"),round(float(v),2)) for i,v in list(cl.items())[-4:]]))
    except Exception as e:
        print("  %-10s errore %s" % (yt,str(e)[:40]))
