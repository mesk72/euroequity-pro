import os, requests, yfinance as yf, pandas as pd
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,exchange,company,yahoo_ticker","ticker":"eq.PDI"}).json()
print("anagrafica:",r)
for x in r:
    ex=x["exchange"]; yt=x.get("yahoo_ticker") or x["ticker"]
    d=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq.PDI","exchange":"eq."+ex,
                "order":"date.desc","limit":"12"}).json()
    print("\nNOSTRI ultimi 12 prezzi (%s.%s):" % (x["ticker"],ex))
    for y in d: print("   %s  %s" % (y["date"],y["adj_close"]))
    print("\nYAHOO (%s):" % yt)
    df=yf.download(yt,period="1mo",interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    for i,v in list(cl.dropna().items())[-12:]: print("   %s  %.4f" % (i.strftime("%Y-%m-%d"),float(v)))
    print("\nSPLIT registrati da Yahoo:")
    try:
        sp=yf.Ticker(yt).splits
        print("   ",sp.tail(5).to_dict() if len(sp) else "nessuno")
    except Exception as e: print("   errore",e)
