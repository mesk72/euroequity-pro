import requests, re, json
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
print("=== 1. PAGINE: rispondono e non sono rotte? ===")
for nome,u in [("home","https://forwardalpha.pro/"),
               ("/value","https://forwardalpha.pro/value"),
               ("/sectors","https://forwardalpha.pro/sectors"),
               ("/research","https://forwardalpha.pro/research"),
               ("/about","https://forwardalpha.pro/about"),
               ("/news","https://forwardalpha.pro/news"),
               ("scheda AAPL","https://forwardalpha.pro/stock/AAPL-US"),
               ("/dividends (eliminata)","https://forwardalpha.pro/dividends")]:
    try:
        r=requests.get(u,timeout=60,headers=UA)
        t=re.sub(r'<script.*?</script>','',r.text,flags=re.S)
        t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t).strip()
        print("  %-24s HTTP %s | %5d car" % (nome,r.status_code,len(t)))
    except Exception as e:
        print("  %-24s ERRORE %s" % (nome,str(e)[:40]))
print()
print("=== 2. API: funziona ancora senza div_yield? ===")
for nome,u in [("singolo titolo","https://forwardalpha.pro/api/db/stocks?ticker=AAPL&exchange=US"),
               ("screener US","https://forwardalpha.pro/api/db/stocks?exchanges=US")]:
    try:
        r=requests.get(u,timeout=90)
        d=r.json(); n=len(d.get("stocks",[]))
        campi=list(d["stocks"][0].keys()) if n else []
        print("  %-16s HTTP %s | titoli: %d | divYield presente: %s" % (nome,r.status_code,n,"divYield" in campi))
    except Exception as e:
        print("  %-16s ERRORE %s" % (nome,str(e)[:50]))
print()
print("=== 3. la sitemap e' ancora integra? ===")
s=requests.get("https://forwardalpha.pro/sitemap.xml",timeout=90).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("  indirizzi: %d | contiene /dividends: %s" % (len(locs), any("dividends" in l for l in locs)))
