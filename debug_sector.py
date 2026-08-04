import yfinance as yf, pandas as pd, os, requests
from datetime import datetime
print("Ora UTC:", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print("Amsterdam/Milano hanno chiuso alle 15:30 UTC")
print()
print("=== Yahoo ha la chiusura del 4 AGOSTO (oggi) per l'Europa? ===")
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
prova=["ASML.AS","SAP.DE","MC.PA","ISP.MI","SHEL.L","NESN.SW","NOKIA.HE","VOLV-B.ST"]
# download di GRUPPO, come fa lo script
df=yf.download(tickers=" ".join(prova),start="2026-07-28",end="2026-08-06",
               interval="1d",auto_adjust=True,progress=False,threads=True)
cl=df["Close"] if isinstance(df.columns,pd.MultiIndex) else df[["Close"]]
for c in prova:
    if c not in cl.columns: print("  %-11s assente" % c); continue
    s=cl[c].dropna()
    date=[i.strftime("%Y-%m-%d") for i in s.index]
    ha3="2026-08-03" in date; ha4="2026-08-04" in date
    ult=" ".join("%s=%.2f" % (s.index[i].strftime("%d/%m"),float(s.iloc[i])) for i in range(max(0,len(s)-3),len(s)))
    print("  %-11s 3/8:%s 4/8:%s | %s" % (c,"SI" if ha3 else "no","SI" if ha4 else "no",ult))
