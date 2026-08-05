import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== Il sito serve i valori della vista? ===")
for tk,ex in [("ASML","AS"),("NESN","SWX"),("AAPL","US")]:
    mv=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price,price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    eod=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    try:
        api=requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=%s"%ex,timeout=60).json()
        r=[x for x in api.get("stocks",[]) if x.get("ticker")==tk]
        scr=(r[0].get("price"),r[0].get("lastPriceDate")) if r else "assente"
    except Exception as e:
        scr="errore"
    print("  %-6s.%-5s vista=%s | storico=%s | screener=%s" % (tk,ex,
        (mv[0]["price"],mv[0]["price_date"]) if mv else "-",
        (eod[0]["adj_close"],eod[0]["date"]) if eod else "-", scr))

print()
print("=== Perche' il recupero scrive zero: provo a riscaricare un titolo SWX mancante ===")
# trova un titolo SWX senza il 4 agosto
uni=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.SWX","in_universe":"eq.true","limit":"1000"}).json()
pres=set(x["ticker"] for x in requests.get(U+"/rest/v1/prices_eod",headers=H,
    params={"select":"ticker","exchange":"eq.SWX","date":"eq.2026-08-04","limit":"1000"}).json())
manc=[x for x in uni if x["ticker"] not in pres][:5]
print("  esempi mancanti al 4/8:", [(x["ticker"],x.get("yahoo_ticker")) for x in manc])
import yfinance as yf, pandas as pd
for x in manc[:3]:
    yt=x.get("yahoo_ticker") or (x["ticker"]+".SW")
    try:
        df=yf.download(yt,start="2026-08-01",end="2026-08-06",interval="1d",auto_adjust=True,progress=False)
        if df.empty: print("    %-12s Yahoo VUOTO" % yt); continue
        cl=df["Close"]
        if isinstance(cl,pd.DataFrame): cl=cl.iloc[:,0]
        cl=cl.dropna()
        print("    %-12s Yahoo: %s" % (yt, [(i.strftime("%d/%m"),round(float(v),2)) for i,v in cl.items()]))
    except Exception as e:
        print("    %-12s errore %s" % (yt,str(e)[:40]))
