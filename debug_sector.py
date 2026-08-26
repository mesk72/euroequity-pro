import requests, re
print("=== il filtro e' arrivato in produzione? ===")
r=requests.get("https://www.forwardalpha.pro/",timeout=60)
chunks=set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text))
trovato=False
for c in list(chunks)[:40]:
    try:
        j=requests.get("https://www.forwardalpha.pro"+c,timeout=25).text
        if "newsTicker" in j or "ALL (" in j:
            trovato=True; break
    except Exception: pass
print("  filtro notizie presente nel codice pubblicato:", trovato)
print()
print("=== il sito risponde correttamente? ===")
for u in ["https://www.forwardalpha.pro/","https://www.forwardalpha.pro/stock/AAPL-US"]:
    rr=requests.get(u,timeout=60)
    print("  %-46s HTTP %s (%d byte)" % (u[:46],rr.status_code,len(rr.text)))
