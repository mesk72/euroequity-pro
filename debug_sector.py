import os, requests, yfinance as yf, pandas as pd
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora UTC:", datetime.utcnow().strftime("%H:%M"), "— Tokyo ha chiuso alle 06:00 UTC")
print()
print("=== Yahoo ha la seduta del 12/8 per Tokyo? ===")
for yt in ["7203.T","6758.T","9984.T"]:
    df=yf.download(yt,start="2026-08-07",end="2026-08-14",interval="1d",auto_adjust=True,progress=False)
    cl=df["Close"]
    if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
    cl=cl.dropna()
    print("  %-8s %s" % (yt,[(i.strftime("%d/%m"),round(float(v),1)) for i,v in cl.items()]))
print()
print("=== e nel nostro database? ===")
for tk in ["7203","6758","9984"]:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq.TSE","order":"date.desc","limit":"3"}).json()
    print("  %-6s %s" % (tk,[(x["date"],x["adj_close"]) for x in r]))
print()
print("=== altri mercati asiatici: hanno il 12/8? ===")
for ex in ["SEHK","ASX","KRX","SGX","TSE"]:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"date":"eq.2026-08-12","limit":"1"})
    print("  %-5s righe al 12/8: %s" % (ex,rc.headers.get("content-range","?").split("/")[-1]))
