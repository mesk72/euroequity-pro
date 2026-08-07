import os, requests, yfinance as yf, pandas as pd, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
lista=["RBTK","EXCE","CXII","ESBA","ANSC","ACGP","MBVI","BCSS","CUSI","DBIN","MCTA","MDRX",
       "FFMR","EVAC","THVB","FINN","EACO","FMBL","SKYC","HBNB","DMII","ROMA","IEAG","QMMM","SIM"]
SED="2026-08-06"
buf=[]; falliti=[]
for tk in lista:
    y=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"yahoo_ticker","ticker":"eq."+tk,"exchange":"eq.US"}).json()
    yt=(y[0].get("yahoo_ticker") if y else None) or tk
    try:
        df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        d={i.strftime("%Y-%m-%d"):float(v) for i,v in cl.items()}
        if SED in d:
            buf.append({"ticker":tk,"exchange":"US","date":SED,"adj_close":round(d[SED],6)})
        else:
            falliti.append(tk)
    except Exception:
        falliti.append(tk)
    time.sleep(0.3)
ok=0
for i in range(0,len(buf),500):
    w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
    if w.status_code in (200,201,204): ok+=len(buf[i:i+500])
print("scritti %d titoli sul %s" % (ok,SED))
if falliti: print("non riusciti:",falliti)
