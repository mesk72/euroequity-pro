import os, requests, csv, io, time
import yfinance as yf, pandas as pd
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').strip()
    try: return float(s)
    except: return None
MAP={"CPSE":"CPSE","OB":"OB"}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
tikr={}
for row in righe:
    t=(row.get("Ticker") or "").strip(); px=(row.get("Primary Exchange") or "").strip()
    v=pn(row.get("Last Mkt Cap",""))
    if t and px in MAP and v: tikr[(t,MAP[px])]=(v,(row.get("Company Name") or ""))

st=[];off=0
while True:
    b=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,exchange,company,yahoo_ticker,in_universe",
                "exchange":"in.(CPSE,OB)","limit":"1000","offset":str(off)},timeout=90).json()
    if not isinstance(b,list) or not b: break
    st+=b; off+=1000
    if len(b)<1000: break

ESCL=["ETF","ETP","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","INVESCO",
      "SPDR","WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","MSCI","INDEX","AMUNDI",
      "SHARES","BITCOIN","ACQUISITION","SOCIMI","OBX"]
def fondo(*n): return any(any(k in (x or "").upper() for k in ESCL) for x in n)

SUF={"CPSE":".CO","OB":".OL"}
cand=[]
for x in st:
    if x.get("in_universe"): continue
    k=(x["ticker"],x["exchange"])
    if k not in tikr: continue
    v,nome=tikr[k]
    if v<300 or fondo(nome,x.get("company")): continue
    cand.append((x["ticker"],x["exchange"],nome,v,x.get("yahoo_ticker")))
print("Da reintegrare: %d" % len(cand))
print()
ok_tot=0
for tk,ex,nome,v,yt_db in cand:
    # codice Yahoo: lo spazio nelle azioni di classe B diventa trattino
    base=tk.replace(" ","-")
    prove=[yt_db] if yt_db else []
    prove += [base+SUF[ex], tk.replace(" ","")+SUF[ex]]
    scelto=None; dati=None
    for yt in [p for p in prove if p]:
        try:
            df=yf.download(yt,period="10d",interval="1d",auto_adjust=True,progress=False)
            if not df.empty:
                cl=df["Close"]
                if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
                if len(cl.dropna())>0: scelto=yt; break
        except Exception: pass
        time.sleep(0.3)
    if not scelto:
        print("  %-10s %-5s %-32s NESSUN CODICE YAHOO FUNZIONANTE" % (tk,ex,nome[:32])); continue
    # storico 5 anni
    inizio=(datetime.utcnow()-timedelta(days=5*365+10)).strftime("%Y-%m-%d")
    df=yf.download(scelto,start=inizio,end=(datetime.utcnow()+timedelta(days=1)).strftime("%Y-%m-%d"),
                   interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    rows={}
    for i,val in cl.items():
        ds=i.strftime("%Y-%m-%d")
        if datetime.utcnow() < datetime.strptime(ds,"%Y-%m-%d").replace(hour=17): continue
        rows[ds]={"ticker":tk,"exchange":ex,"date":ds,"adj_close":round(float(val),6)}
    rows=list(rows.values()); n=0
    for i in range(0,len(rows),500):
        w=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",headers=HU,json=rows[i:i+500])
        if w.status_code in (200,201,204): n+=len(rows[i:i+500])
    requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+tk,"exchange":"eq."+ex},
        json={"in_universe":True,"yahoo_ticker":scelto})
    ok_tot+=1
    print("  %-10s %-5s %-32s %7.0f MM  codice=%-12s %4d sedute" % (tk,ex,nome[:32],v,scelto,n))
    time.sleep(0.5)
print()
print("REINTEGRATI: %d" % ok_tot)
