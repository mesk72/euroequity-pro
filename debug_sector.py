import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1)"}
print("=== 1. la sitemap ora indica il dominio giusto? ===")
s=requests.get("https://www.forwardalpha.pro/sitemap.xml",timeout=120).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("  indirizzi totali: %d" % len(locs))
print("  con www:     %d" % sum(1 for l in locs if l.startswith("https://www.")))
print("  senza www:   %d" % sum(1 for l in locs if not l.startswith("https://www.")))
spazi=[l for l in locs if " " in l]
print("  con spazi grezzi (non validi): %d" % len(spazi))
print("  esempi ticker particolari:")
for l in [x for x in locs if "%20" in x or "%2E" in x][:5]: print("     ",l)
print()
print("=== 2. gli indirizzi della sitemap rispondono 200 senza rimbalzi? ===")
for u in locs[:3]+[l for l in locs if "%20" in l][:2]:
    r=requests.get(u,timeout=60,headers=UA,allow_redirects=False)
    print("  HTTP %s  %s" % (r.status_code,u[:66]))
print()
print("=== 3. il canonical punta al dominio che serve? ===")
r=requests.get("https://www.forwardalpha.pro/stock/AAPL-US",timeout=60,headers=UA)
m=re.search(r'<link rel="canonical" href="([^"]+)"',r.text)
print("  canonical:", m.group(1) if m else "assente")
print("  HTTP:",r.status_code,"| testo leggibile:",len(re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>','',r.text,flags=re.S))))
print()
print("=== 4. robots.txt ===")
print(requests.get("https://www.forwardalpha.pro/robots.txt",timeout=30).text)
