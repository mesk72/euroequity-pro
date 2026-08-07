import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

print("=== A. LA VISTA E' FERMA? Confronto storico vs vista ===")
for ex in ["MIL","XETRA","PA","SWX","HE","US","TSE"]:
    eod=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    mv=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
            params={"select":"price_date","exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        mv+=[x["price_date"] for x in b]; off+=1000
        if len(b)<1000: break
    c=Counter(mv)
    print("  %-6s storico=%s | vista=%s (%d titoli)" % (ex,
        eod[0]["date"] if eod else "-", max(c) if c else "-", c.get(max(c),0) if c else 0))

print()
print("=== B. Quanti titoli MIL hanno il 6/8 nello storico? ===")
for ex in ["MIL","XETRA","PA"]:
    r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq.2026-08-06","limit":"1"})
    print("  %-6s %s righe al 6/8" % (ex,r.headers.get("content-range","?").split("/")[-1]))

print()
print("=== C. I 'non disponibili' svizzeri lo sono davvero? ===")
r=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.SWX","in_universe":"eq.true","limit":"6"}).json()
for x in r:
    yt=x.get("yahoo_ticker") or (x["ticker"]+".SW")
    try:
        df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        d=[i.strftime("%d/%m") for i in cl.index]
        print("   %-12s ultime: %s" % (yt,d[-4:]))
    except Exception as e:
        print("   %-12s errore" % yt)
    time.sleep(0.4)
