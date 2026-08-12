import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
def leggi(tab,ex,campi):
    o=[];f=0
    while True:
        r=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"exchange":"eq."+ex,"limit":"1000","offset":str(f)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        o+=b; f+=1000
        if len(b)<1000: break
    return o

recup=0; nonrec=[]
for ex in EX:
    mv=leggi("latest_prices_mv",ex,"ticker,price_date")
    if not mv: continue
    sed=Counter(x["price_date"] for x in mv).most_common(1)[0][0]
    indietro=[x["ticker"] for x in mv if x["price_date"]<sed]
    if not indietro: continue
    buf=[]
    for tk in indietro:
        y=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"yahoo_ticker,company","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
        yt=(y[0].get("yahoo_ticker") if y else None) or tk
        az=(y[0].get("company") if y else "") or ""
        try:
            df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            d={i.strftime("%Y-%m-%d"):float(v) for i,v in cl.items()}
            if sed in d:
                buf.append({"ticker":tk,"exchange":ex,"date":sed,"adj_close":round(d[sed],6)})
            else:
                nonrec.append((tk,ex,az[:32],max(d) if d else "nessuna"))
        except Exception:
            nonrec.append((tk,ex,az[:32],"errore"))
        time.sleep(0.2)
    for i in range(0,len(buf),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
        if w.status_code in (200,201,204): recup+=len(buf[i:i+500])
    print("%-6s indietro %3d -> recuperati %3d" % (ex,len(indietro),len(buf)))

print()
print("TOTALE RECUPERATI: %d" % recup)
print()
print("=== NON recuperabili: Yahoo non ha la seduta (%d) ===" % len(nonrec))
for tk,ex,az,u in nonrec[:40]:
    print("  %-10s %-6s %-32s yahoo si ferma a %s" % (tk,ex,az,u))
if len(nonrec)>40: print("  ...e altri %d" % (len(nonrec)-40))
