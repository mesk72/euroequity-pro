import requests, re
print("=== Cosa dicono le pagine vere del sito ai motori di ricerca? ===")
pagine=[("home","https://forwardalpha.pro/"),
        ("screens","https://forwardalpha.pro/screens"),
        ("research","https://forwardalpha.pro/research"),
        ("about","https://forwardalpha.pro/about"),
        ("titolo AAPL","https://forwardalpha.pro/stock/AAPL-US"),
        ("news","https://forwardalpha.pro/news")]
for nome,u in pagine:
    try:
        r=requests.get(u,timeout=40)
        xr=r.headers.get("x-robots-tag","(nessuno)")
        m=re.search(r'<meta[^>]*name=["\']robots["\'][^>]*>', r.text, re.I)
        meta=m.group()[:90] if m else "(nessun meta robots)"
        print("  %-12s HTTP %s | header: %-12s | %s" % (nome,r.status_code,xr,meta))
    except Exception as e:
        print("  %-12s errore %s" % (nome,str(e)[:40]))
print()
print("=== quante pagine dichiara la sitemap ===")
s=requests.get("https://forwardalpha.pro/sitemap.xml",timeout=40).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("  totale:",len(locs))
tipi={}
for l in locs:
    p=l.replace("https://forwardalpha.pro","").split("/")
    k=p[1] if len(p)>1 and p[1] else "(home)"
    tipi[k]=tipi.get(k,0)+1
for k,v in sorted(tipi.items(),key=lambda x:-x[1])[:8]:
    print("   %-14s %d" % (k,v))
