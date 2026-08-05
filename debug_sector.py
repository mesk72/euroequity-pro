import os, requests, yfinance as yf, pandas as pd, random
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
      "— la seduta del 4/8 e' chiusa da ~15 ore")
print()
# titoli grandi vs titoli qualsiasi, stesso mercato
grandi=[("ASML.AS","AS"),("MC.PA","PA"),("ISP.MI","MIL"),("SHEL.L","LSE"),("SAP.DE","XETRA")]
r=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"ticker,exchange,mkt_cap","exchange":"in.(AS,PA,MIL,LSE,XETRA)",
            "order":"mkt_cap.asc","limit":"400"})
piccoli=[x for x in r.json() if x.get("mkt_cap")][:200]
random.seed(7); random.sample(piccoli,min(15,len(piccoli)))
suf={"AS":".AS","PA":".PA","MIL":".MI","LSE":".L","XETRA":".DE"}
camp=[(x["ticker"]+suf[x["exchange"]],x["exchange"]) for x in random.sample(piccoli,15)]

def quanti(lista,eti):
    ok=0;tot=0
    for yt,ex in lista:
        try:
            d=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
            if d.empty: tot+=1; continue
            cl=d["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            date=[i.strftime("%Y-%m-%d") for i in cl.dropna().index]
            tot+=1
            if "2026-08-04" in date: ok+=1
        except Exception: tot+=1
    print("  %-28s %2d/%2d hanno il 4 agosto" % (eti,ok,tot))

quanti(grandi,"5 grandi (blue chip)")
quanti(camp,"15 a bassa capitalizzazione")
