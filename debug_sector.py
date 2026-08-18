import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
def leggi(tab,ex,c):
    o=[];f=0
    while True:
        r=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":c,"exchange":"eq."+ex,"limit":"1000","offset":str(f)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        o+=b; f+=1000
        if len(b)<1000: break
    return o

indietro=[]
for ex in EX:
    mv=leggi("latest_prices_mv",ex,"ticker,price_date")
    if not mv: continue
    sed=Counter(x["price_date"] for x in mv).most_common(1)[0][0]
    for x in mv:
        if x["price_date"]<sed: indietro.append((ex,x["ticker"],x["price_date"],sed))
print("TOTALE non allineati: %d" % len(indietro))
print()
nostri=[];loro=[]
for ex,tk,nostro,sed in indietro:
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
        if sed in d: nostri.append({"ticker":tk,"exchange":ex,"date":sed,"adj_close":round(d[sed],6),"az":az})
        else: loro.append((tk,ex,az[:30],nostro,max(d) if d else "nessuna"))
    except Exception:
        loro.append((tk,ex,az[:30],nostro,"errore"))
    time.sleep(0.2)

print("=== COLPA NOSTRA (Yahoo ha il dato): %d ===" % len(nostri))
for x in nostri: print("  %-10s %-6s %-30s" % (x["ticker"],x["exchange"],x["az"][:30]))
if nostri:
    buf=[{k:v for k,v in x.items() if k!="az"} for x in nostri]
    ok=0
    for i in range(0,len(buf),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=buf[i:i+500])
        if w.status_code in (200,201,204): ok+=len(buf[i:i+500])
    print("  -> RECUPERATI: %d" % ok)
print()
print("=== Yahoo NON ha il dato: %d ===" % len(loro))
from collections import Counter as C2
print("  per mercato:", dict(C2(x[1] for x in loro)))
