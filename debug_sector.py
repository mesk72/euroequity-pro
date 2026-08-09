import requests, re, json
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
for u in ["https://forwardalpha.pro/stock/AAPL-US","https://forwardalpha.pro/stock/ASML-AS"]:
    r=requests.get(u,timeout=60,headers=UA)
    h=r.text
    print("===",u,"===")
    t=re.search(r"<title>(.*?)</title>",h,re.S)
    print("  titolo:",(t.group(1) if t else "-")[:120])
    d=re.search(r'<meta name="description" content="(.*?)"',h,re.S)
    print("  descrizione:",(d.group(1) if d else "-")[:260])
    j=re.search(r'application/ld\+json"[^>]*>(.*?)</script>',h,re.S)
    print("  dati strutturati:", "presenti" if j else "ASSENTI")
    if j:
        try: print("   ",json.dumps(json.loads(j.group(1)),ensure_ascii=False)[:200])
        except Exception: pass
    # controllo che i punteggi NON siano esposti
    esposti=[p for p in ["Value Score 9","Value Score 8","Value Score 7","valueScore\":"] if p in h]
    print("  punteggi numerici esposti:", esposti if esposti else "nessuno")
    print()
