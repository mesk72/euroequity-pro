import os, requests, yfinance as yf, pandas as pd
from datetime import datetime
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Ora test (UTC):", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
print()
print("=== YAHOO: ha la chiusura di LUNEDI 3 AGOSTO per l'Europa? ===")
prova=[("ASML.AS","AS","ASML"),("SAP.DE","XETRA","SAP"),("MC.PA","PA","MC"),
       ("SHEL.L","LSE","SHEL"),("ISP.MI","MIL","ISP"),("NESN.SW","SWX","NESN"),
       ("NOKIA.HE","HE","NOKIA"),("VOLV-B.ST","OM","VOLV B")]
for yt,ex,tk in prova:
    try:
        df=yf.download(yt,period="8d",interval="1d",auto_adjust=True,progress=False)
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        date_y=[cl.index[i].strftime("%Y-%m-%d") for i in range(len(cl))]
        ha3="2026-08-03" in date_y
        ultime=" ".join("%s=%.2f" % (cl.index[i].strftime("%d/%m"),float(cl.iloc[i])) for i in range(max(0,len(cl)-3),len(cl)))
        # cosa abbiamo noi
        r=requests.get(U+"/rest/v1/prices_eod",headers=H,
            params={"select":"date","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"})
        d=r.json()
        nostro=d[0]["date"] if isinstance(d,list) and d else "-"
        print("  %-11s yahoo ha 3/8: %-3s | nostro DB: %s | yahoo: %s" % (yt,"SI" if ha3 else "NO",nostro,ultime))
    except Exception as e:
        print("  %-11s errore %s" % (yt,str(e)[:50]))
