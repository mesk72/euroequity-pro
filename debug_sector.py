import requests, re, os
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
HS={"apikey":SK,"Authorization":"Bearer "+SK}

r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}

print("=== 1. UN ANONIMO PUO' ANCORA LEGGERE? ===")
for t in ["stocks","fundamentals","prices_eod","latest_prices","top500_universe","sector_quintile_partials"]:
    rr=requests.get(BASE+"/rest/v1/"+t,headers=HA,params={"select":"*","limit":"2"},timeout=25)
    try: n=len(rr.json()) if isinstance(rr.json(),list) else -1
    except Exception: n=-1
    esito="CHIUSA" if n==0 else ("ANCORA APERTA (%d righe)"%n if n>0 else "HTTP %s"%rr.status_code)
    print("  %-26s %s" % (t,esito))

print()
print("=== 2. GLI SCRIPT NOTTURNI FUNZIONANO ANCORA? (chiave di servizio) ===")
for t in ["stocks","prices_eod","latest_prices"]:
    rr=requests.get(BASE+"/rest/v1/"+t,headers=HS,params={"select":"*","limit":"1"},timeout=25)
    try: n=len(rr.json()) if isinstance(rr.json(),list) else 0
    except Exception: n=0
    print("  lettura %-16s %s" % (t,"OK" if n>0 else "PROBLEMA HTTP %s"%rr.status_code))
# prova di scrittura con chiave di servizio
esca={"ticker":"__WTEST__","exchange":"SGX","price":1.0,"price_date":"2020-01-01"}
w=requests.post(BASE+"/rest/v1/latest_prices?on_conflict=ticker,exchange",
    headers={**HS,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"},
    json=[esca],timeout=25)
print("  scrittura latest_prices  %s" % ("OK" if w.status_code in (200,201,204) else "PROBLEMA HTTP %s"%w.status_code))
requests.delete(BASE+"/rest/v1/latest_prices",headers=HS,params={"ticker":"eq.__WTEST__"},timeout=20)

print()
print("=== 3. IL SITO FUNZIONA? ===")
for nome,url in [("homepage","https://forwardalpha.pro/"),
                 ("api titoli US","https://forwardalpha.pro/api/db/stocks?exchanges=US"),
                 ("api storico AAPL","https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=400")]:
    try:
        rr=requests.get(url,timeout=60)
        extra=""
        if "api/db/stocks" in url:
            try: extra=" - %d titoli" % len(rr.json().get("stocks",[]))
            except Exception: pass
        if "history" in url:
            try: extra=" - %d prezzi" % len(rr.json().get("history",[]))
            except Exception: pass
        print("  %-18s HTTP %s%s" % (nome,rr.status_code,extra))
    except Exception as e:
        print("  %-18s errore %s" % (nome,str(e)[:40]))
