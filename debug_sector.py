import os, requests, yfinance as yf, pandas as pd, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Chi e' fermo al 4/8: Yahoo ha il 5/8 per loro?")
for ex in ["TSE","SEHK"]:
    r=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"ticker","exchange":"eq."+ex,"price_date":"eq.2026-08-04","limit":"600"})
    tk=[x["ticker"] for x in r.json()][:6]
    print("\n=== %s (campione di %d su quelli fermi) ===" % (ex,len(tk)))
    for t in tk:
        y=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"yahoo_ticker","ticker":"eq."+t,"exchange":"eq."+ex}).json()
        yt=y[0].get("yahoo_ticker") if y else None
        if not yt: print("   %-8s nessun codice Yahoo" % t); continue
        try:
            df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
            if df.empty: print("   %-10s Yahoo VUOTO" % yt); continue
            cl=df["Close"]
            if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
            cl=cl.dropna()
            date=[i.strftime("%Y-%m-%d") for i in cl.index]
            ha5="2026-08-05" in date
            print("   %-10s Yahoo ha il 5/8: %-3s | ultime: %s" % (yt,"SI" if ha5 else "NO",
                  [(cl.index[i].strftime("%d/%m"),round(float(cl.iloc[i]),2)) for i in range(max(0,len(cl)-3),len(cl))]))
        except Exception as e:
            print("   %-10s errore %s" % (yt,str(e)[:40]))
        time.sleep(0.4)
