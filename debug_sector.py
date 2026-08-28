import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
def leggi(tab,ex,campi,extra=None):
    o=[];off=0
    while True:
        p={"select":campi,"exchange":"eq."+ex,"limit":"1000","offset":str(off)}
        if extra: p.update(extra)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=len(b)
    return o
rec=0; nonrec=0
for ex in EX:
    mv=leggi("latest_prices_mv",ex,"ticker,price_date")
    if not mv: continue
    sed=Counter(x["price_date"] for x in mv).most_common(1)[0][0]
    indietro=[x["ticker"] for x in mv if x["price_date"]<sed]
    if not indietro: continue
    buf=[]
    for tk in indietro:
        y=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"yahoo_ticker","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
        yt=(y[0].get("yahoo_ticker") if y else None) or tk
        try:
            df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            d={i.strftime("%Y-%m-%d"):float(v) for i,v in cl.dropna().items()}
            if sed in d:
                buf.append({"ticker":tk,"exchange":ex,"date":sed,"adj_close":round(d[sed],6)})
            else: nonrec+=1
        except Exception: nonrec+=1
        time.sleep(0.2)
    ok=0
    for i in range(0,len(buf),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
        if w.status_code in (200,201,204): ok+=len(buf[i:i+500])
    rec+=ok
    if ok or indietro: print("%-6s indietro %3d -> recuperati %3d" % (ex,len(indietro),ok))
print()
print("TOTALE recuperati: %d | non disponibili su Yahoo: %d" % (rec,nonrec))
