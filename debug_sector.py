import requests, re, json
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}

print("=== 1. UN ATTACCANTE COSA RIESCE A LEGGERE ORA? ===")
for t in ["stocks","fundamentals","prices_eod","latest_prices",
          "top500_universe","sector_quintile_partials","watchlist","profiles"]:
    try:
        rr=requests.get(BASE+"/rest/v1/"+t,headers=HA,params={"select":"*","limit":"3"},timeout=25)
        try: n=len(rr.json()) if isinstance(rr.json(),list) else 0
        except Exception: n=0
        stato="APERTA (%d righe)" % n if n>0 else "chiusa"
        print("  %-26s HTTP %s  -> %s" % (t,rr.status_code,stato))
    except Exception as e:
        print("  %-26s errore" % t)

print()
print("=== 2. SCRITTURA/CANCELLAZIONE anonima ancora bloccata? ===")
w=requests.post(BASE+"/rest/v1/stocks",headers={**HA,"Content-Type":"application/json"},
    json=[{"ticker":"__X__","exchange":"__X__"}],timeout=20)
print("  INSERT stocks -> HTTP %s %s" % (w.status_code, "BLOCCATO" if w.status_code>=400 else "!!! PERMESSO !!!"))

print()
print("=== 3. IL SITO FUNZIONA ANCORA? ===")
for nome,url in [("homepage","https://forwardalpha.pro/"),
                 ("API titoli US","https://forwardalpha.pro/api/db/stocks?exchanges=US"),
                 ("API singolo titolo","https://forwardalpha.pro/api/db/stocks?ticker=AAPL&exchange=US"),
                 ("API grafico","https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=400")]:
    try:
        rr=requests.get(url,timeout=60)
        extra=""
        if "api/db/stocks" in url:
            try:
                d=rr.json(); extra=" | titoli restituiti: %d" % len(d.get("stocks",[]))
            except Exception: pass
        if "history" in url:
            try:
                d=rr.json(); extra=" | punti storico: %d" % len(d.get("history",[]))
            except Exception: pass
        print("  %-20s HTTP %s%s" % (nome,rr.status_code,extra))
    except Exception as e:
        print("  %-20s ERRORE %s" % (nome,str(e)[:40]))
