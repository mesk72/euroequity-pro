import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
SED="2026-08-07"
tot=0
for ex in EX:
    mv=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"ticker,price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        mv+=b; off+=1000
        if len(b)<1000: break
    manc=[x["ticker"] for x in mv if x["price_date"]<SED]
    if not manc: continue
    buf=[]
    for tk in manc:
        y=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"yahoo_ticker","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
        yt=(y[0].get("yahoo_ticker") if y else None) or tk
        try:
            df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            d={i.strftime("%Y-%m-%d"):float(v) for i,v in cl.items()}
            if SED in d:
                buf.append({"ticker":tk,"exchange":ex,"date":SED,"adj_close":round(d[SED],6)})
        except Exception: pass
        time.sleep(0.22)
    ok=0
    for i in range(0,len(buf),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
        if w.status_code in (200,201,204): ok+=len(buf[i:i+500])
    tot+=ok
    if ok or manc: print("%-6s indietro %3d -> recuperati %3d" % (ex,len(manc),ok))
print("\nTOTALE recuperati: %d" % tot)
