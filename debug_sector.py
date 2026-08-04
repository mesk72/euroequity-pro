import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("Confronto: quello che dice il DATABASE vs quello che serve l'API del sito")
print("(SAP, LVMH, Apple, Intesa erano tra i 6.886 esclusi dal taglio a 1000)")
print()
for tk,ex in [("SAP","XETRA"),("MC","PA"),("AAPL","US"),("ISP","MIL"),("ASML","AS")]:
    eod=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,
                "order":"date.desc","limit":"1"}).json()
    lp=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"price,price_date","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    try:
        api=requests.get("https://forwardalpha.pro/api/db/stocks?ticker=%s&exchange=%s"%(tk,ex),timeout=45).json()
        s=(api.get("stocks") or [{}])[0]
        apip=s.get("price"); apid=s.get("lastPriceDate")
    except Exception as e:
        apip=apid="errore"
    e0=(eod[0]["adj_close"],eod[0]["date"]) if eod else "-"
    l0=(lp[0]["price"],lp[0]["price_date"]) if lp else "-"
    ok = "OK" if (apip is not None and eod and abs(float(apip)-float(eod[0]["adj_close"]))<0.01) else "DIVERGE"
    print("  %-6s.%-6s grafico(prices_eod)=%s | cache=%s | API sito=%s %s  -> %s" %
          (tk,ex,e0,l0,apip,apid,ok))
