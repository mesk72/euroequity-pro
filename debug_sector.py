import os, requests, time
import yfinance as yf, pandas as pd
from datetime import datetime, timedelta

U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

TITOLI=["MBH3","SPB","EUK3","BFV","PHH2","HG1","WBAH","SIM0","LEC","T2G","MNV6","SSH","NLM"]
EX="XETRA"
ORA_LIMITE_UTC=17   # stesso blocco degli script: solo sedute europee chiuse

def seduta_conclusa(ds):
    try: d=datetime.strptime(ds,"%Y-%m-%d")
    except Exception: return False
    return datetime.utcnow() >= d.replace(hour=ORA_LIMITE_UTC,minute=0,second=0)

print("Ora (UTC):", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print("\n=== 1. Aggiorno yahoo_ticker da .DE a .F ===")
for tk in TITOLI:
    r=requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+tk,"exchange":"eq."+EX},
        json={"yahoo_ticker":tk+".F"})
    print("  %-6s -> %s.F   HTTP %s" % (tk,tk,r.status_code))

print("\n=== 2. Scarico 5 anni di storico da Francoforte ===")
inizio=(datetime.utcnow()-timedelta(days=5*365+10)).strftime("%Y-%m-%d")
fine=(datetime.utcnow()+timedelta(days=2)).strftime("%Y-%m-%d")
tot_scritte=0; tot_saltate=0
for tk in TITOLI:
    try:
        df=yf.download(tk+".F",start=inizio,end=fine,interval="1d",
                       auto_adjust=True,progress=False)
        if df.empty:
            print("  %-6s VUOTO" % tk); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        righe=[]; saltate=0
        for idx,val in cl.items():
            ds=idx.strftime("%Y-%m-%d")
            if not seduta_conclusa(ds):
                saltate+=1; continue
            righe.append({"ticker":tk,"exchange":EX,"date":ds,
                          "adj_close":round(float(val),6)})
        # dedup di sicurezza
        d={}
        for r0 in righe: d[(r0["ticker"],r0["exchange"],r0["date"])]=r0
        righe=list(d.values())
        scritte=0
        for i in range(0,len(righe),500):
            rw=requests.post(U+"/rest/v1/prices_eod?on_conflict=ticker,exchange,date",
                             headers=HU,json=righe[i:i+500])
            if rw.status_code in (200,201,204): scritte+=len(righe[i:i+500])
            else: print("     ERRORE HTTP %s: %s" % (rw.status_code, rw.text[:120]))
        tot_scritte+=scritte; tot_saltate+=saltate
        print("  %-6s %4d righe scritte (%s -> %s)%s" % (
            tk,scritte,
            righe[0]["date"] if righe else "-",
            righe[-1]["date"] if righe else "-",
            "  [saltate %d: seduta aperta]" % saltate if saltate else ""))
    except Exception as e:
        print("  %-6s ERRORE %s" % (tk,str(e)[:70]))
    time.sleep(1)

print("\nTotale righe storiche scritte: %d   saltate per seduta aperta: %d" % (tot_scritte,tot_saltate))

print("\n=== 3. Aggiorno la cache dei prezzi ===")
batch=[]
for tk in TITOLI:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+EX,
                "order":"date.desc","limit":"2"})
    rows=r.json()
    if not isinstance(rows,list) or not rows: continue
    u=rows[0]; p=rows[1] if len(rows)>1 else None
    chg=round(u["adj_close"]/p["adj_close"]-1,6) if (p and p.get("adj_close")) else None
    pp=(u["adj_close"]/(1+chg)) if (chg is not None and (1+chg)!=0) else None
    batch.append({"ticker":tk,"exchange":EX,"price":u["adj_close"],"prev_price":pp,
                  "price_date":u["date"],"change1d":chg})
rw=requests.post(U+"/rest/v1/latest_prices?on_conflict=ticker,exchange",headers=HU,json=batch)
print("  cache aggiornata per %d titoli (HTTP %s)" % (len(batch),rw.status_code))

print("\n=== 4. VERIFICA FINALE ===")
for tk in TITOLI:
    rc=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+EX,"limit":"1"})
    n=rc.headers.get("content-range","0/0").split("/")[-1]
    r1=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+EX,"order":"date.asc","limit":"1"}).json()
    r2=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"price_date,price","ticker":"eq."+tk,"exchange":"eq."+EX}).json()
    print("  %-6s storico:%5s righe da %s   cache: %s" % (
        tk,n,r1[0]["date"] if r1 else "-",
        (r2[0]["price_date"],r2[0]["price"]) if r2 else "ASSENTE"))
