import requests, re
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
print("=== IL SITO FUNZIONA? ===")
prove=[("homepage","https://forwardalpha.pro/",None),
       ("titoli US","https://forwardalpha.pro/api/db/stocks?exchanges=US","stocks"),
       ("titoli Global","https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX","stocks"),
       ("storico AAPL","https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=400","history"),
       ("indici","https://forwardalpha.pro/api/db/indices",None)]
for nome,url,campo in prove:
    try:
        r=requests.get(url,timeout=70)
        extra=""
        if campo:
            try: extra=" - %d elementi" % len(r.json().get(campo,[]))
            except Exception: pass
        print("  %-16s HTTP %s%s" % (nome,r.status_code,extra))
    except Exception as e:
        print("  %-16s errore %s" % (nome,str(e)[:45]))

print()
print("=== I DATI SONO ANCORA CHIUSI AL PUBBLICO? ===")
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}
for t in ["stocks","fundamentals","prices_eod","latest_prices","top500_universe"]:
    rr=requests.get(BASE+"/rest/v1/"+t,headers=HA,params={"select":"*","limit":"2"},timeout=25)
    try: n=len(rr.json()) if isinstance(rr.json(),list) else -1
    except Exception: n=-1
    print("  %-20s %s" % (t,"CHIUSA" if n==0 else ("APERTA! %d righe"%n if n>0 else "HTTP %s"%rr.status_code)))
