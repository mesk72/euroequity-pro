import os, requests, yfinance as yf, pandas as pd, time
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
    "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
def leggi(tab,ex,campi):
    out=[];off=0
    while True:
        r=requests.get(U+"/rest/v1/"+tab,headers=H,
            params={"select":campi,"exchange":"eq."+ex,"limit":"1000","offset":str(off)})
        b=r.json()
        if not isinstance(b,list) or not b: break
        out+=b; off+=1000
        if len(b)<1000: break
    return out

indietro=[]
for ex in EX:
    mv=leggi("latest_prices_mv",ex,"ticker,price_date")
    if not mv: continue
    c=Counter(x["price_date"] for x in mv)
    top=max(c)
    for x in mv:
        if x["price_date"]=="2026-08-06":
            indietro.append((ex,x["ticker"],x["price_date"],top))
print("Titoli fermi al 6 agosto: %d" % len(indietro))
print()
nostri=[];loro=[]
for ex,tk,nostro,top in indietro:
    y=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"yahoo_ticker,company","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    yt=(y[0].get("yahoo_ticker") if y else None) or tk
    az=(y[0].get("company") if y else "") or ""
    try:
        df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        date=[i.strftime("%Y-%m-%d") for i in cl.index]
        if "2026-08-07" in date:
            nostri.append((ex,tk,az,float(cl.iloc[date.index("2026-08-07")])))
        else:
            loro.append((ex,tk,az,date[-1] if date else "nessuna"))
    except Exception:
        loro.append((ex,tk,az,"errore"))
    time.sleep(0.25)

print("=== COLPA NOSTRA: Yahoo ha il 7/8 e noi no (%d) ===" % len(nostri))
for ex,tk,az,v in nostri: print("  %-9s %-6s %-34s yahoo=%.2f" % (tk,ex,az[:34],v))
print()
print("=== Yahoo non ha il 7/8 (%d) ===" % len(loro))
for ex,tk,az,u in loro[:25]: print("  %-9s %-6s %-34s ultima: %s" % (tk,ex,az[:34],u))
if len(loro)>25: print("  ...e altri %d" % (len(loro)-25))
