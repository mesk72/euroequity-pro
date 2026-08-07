import os, requests, yfinance as yf, pandas as pd
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print()
print("=== Yahoo ha il 6 e il 7 agosto per Milano/Parigi/Francoforte? ===")
for yt in ["ISP.MI","ENI.MI","MC.PA","OR.PA","SAP.DE","BMW.DE"]:
    df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    print("  %-8s %s" % (yt,[(i.strftime("%d/%m"),round(float(v),2)) for i,v in list(cl.items())[-3:]]))
print()
print("=== cosa dice il log EU sul download principale ===")
r=requests.get(U+"/rest/v1/script_logs",headers=H,
    params={"select":"created_at,log_text","script_name":"eq.daily_eu_yahoo","order":"created_at.desc","limit":"1"}).json()
print("eseguito:",r[0]["created_at"][:19])
for riga in r[0]["log_text"].split("\n"):
    if any(k in riga for k in ["Prezzi Yahoo","BLOCCO SICUREZZA","Data piu' recente nel mercato MIL","Data piu' recente nel mercato PA","scartate"]):
        print("  ",riga.strip()[:130])
