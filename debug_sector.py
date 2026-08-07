import os, requests, yfinance as yf, pandas as pd, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
TARGET="2026-08-06"
tot=0
for ex in EU:
    pres=set(); off=0
    while True:
        b=requests.get(U+"/rest/v1/prices_eod",headers=H,
            params={"select":"ticker","exchange":"eq."+ex,"date":"eq."+TARGET,"limit":"1000","offset":str(off)}).json()
        if not isinstance(b,list) or not b: break
        pres.update(x["ticker"] for x in b); off+=1000
        if len(b)<1000: break
    uni=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,yahoo_ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1000","offset":str(off)}).json()
        if not isinstance(b,list) or not b: break
        uni+=b; off+=1000
        if len(b)<1000: break
    manc=[x for x in uni if x["ticker"] not in pres]
    if not manc: continue
    buf=[]
    for i in range(0,len(manc),40):
        m={}
        for x in manc[i:i+40]:
            yt=x.get("yahoo_ticker")
            if yt: m[yt]=x["ticker"]
        if not m: continue
        try:
            df=yf.download(tickers=" ".join(m.keys()),start="2026-08-05",end="2026-08-07",
                           interval="1d",auto_adjust=True,progress=False,threads=True)
            if df.empty: continue
            cl=df["Close"] if isinstance(df.columns,pd.MultiIndex) else df[["Close"]].rename(columns={"Close":list(m)[0]})
            for yt,tk in m.items():
                if yt not in cl.columns: continue
                for idx,pr in cl[yt].dropna().items():
                    if idx.strftime("%Y-%m-%d")==TARGET:
                        buf.append({"ticker":tk,"exchange":ex,"date":TARGET,"adj_close":round(float(pr),6)})
        except Exception: pass
        time.sleep(1.0)
    d={}
    for r in buf: d[(r["ticker"],r["exchange"],r["date"])]=r
    buf=list(d.values()); ok=0
    for i in range(0,len(buf),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
        if w.status_code in (200,201,204): ok+=len(buf[i:i+500])
    tot+=ok
    print("%-6s mancavano %4d -> scaricati %4d" % (ex,len(manc),ok))
print("\nTOTALE recuperati: %d" % tot)
