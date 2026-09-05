import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1)"}
print("=== il tag noindex e' presente? ===")
for nome,u in [("homepage","https://www.forwardalpha.pro/"),
               ("scheda AAPL","https://www.forwardalpha.pro/stock/AAPL-US"),
               ("/value","https://www.forwardalpha.pro/value"),
               ("/sectors","https://www.forwardalpha.pro/sectors")]:
    r=requests.get(u,timeout=60,headers=UA)
    m=re.search(r'<meta name="robots" content="([^"]*)"',r.text)
    xr=r.headers.get("x-robots-tag","")
    print("  %-14s meta: %-28s header: %s" % (nome,(m.group(1) if m else "ASSENTE"),xr or "-"))
print()
print("=== la sitemap contiene ancora le schede titolo? ===")
s=requests.get("https://www.forwardalpha.pro/sitemap.xml",timeout=90).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("  indirizzi:",len(locs))
for l in locs[:5]: print("   ",l)
print()
print("=== robots.txt consente la scansione (necessario per il noindex)? ===")
print(requests.get("https://www.forwardalpha.pro/robots.txt",timeout=30).text[:300])
