import os, requests, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

TODAY=datetime.now().strftime("%Y-%m-%d")
END_FOR_DOWNLOAD=(datetime.now()+timedelta(days=2)).strftime("%Y-%m-%d")
ORA_LIMITE_UTC=17
def seduta_conclusa(ds):
    d=datetime.strptime(ds,"%Y-%m-%d")
    return datetime.utcnow()>=d.replace(hour=ORA_LIMITE_UTC,minute=0,second=0)

print("TODAY =",TODAY," END_FOR_DOWNLOAD =",END_FOR_DOWNLOAD)
print("utcnow =",datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print("seduta_conclusa('2026-08-03') =",seduta_conclusa("2026-08-03"))
print("seduta_conclusa('2026-08-04') =",seduta_conclusa("2026-08-04"))
print()

ex="AS"
rg=requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"date","exchange":"eq."+ex,"order":"date.desc","limit":"1"})
most_recent=rg.json()[0]["date"]
safety=(datetime.strptime(most_recent,"%Y-%m-%d")-timedelta(days=10)).strftime("%Y-%m-%d")
start_dt=(datetime.strptime(safety,"%Y-%m-%d")+timedelta(days=1)).strftime("%Y-%m-%d")
print("Mercato %s: most_recent=%s  base=%s  start_dt=%s" % (ex,most_recent,safety,start_dt))
print("  last_dates >= TODAY ? %s  (se SI il titolo viene SALTATO)" % (safety>=TODAY))
print()

df=yf.download(tickers="ASML.AS PHIA.AS",start=start_dt,end=END_FOR_DOWNLOAD,
               interval="1d",auto_adjust=True,progress=False,threads=True)
print("colonne:",type(df.columns).__name__)
closes=df["Close"] if isinstance(df.columns,pd.MultiIndex) else df[["Close"]]
print("colonne closes:",list(closes.columns))
for yt in ["ASML.AS"]:
    if yt not in closes.columns:
        print("  %s NON presente!" % yt); continue
    s=closes[yt].dropna()
    print("\n  %s — decisione riga per riga (last=%s):" % (yt,safety))
    for idx,pr in list(s.items())[-6:]:
        ds=idx.strftime("%Y-%m-%d")
        scarta_last = ds<=safety
        scarta_guard = not seduta_conclusa(ds)
        esito="SCARTATA (gia' presente)" if scarta_last else ("SCARTATA (seduta aperta)" if scarta_guard else "SCRITTA")
        print("    %s  %.2f  -> %s" % (ds,float(pr),esito))
