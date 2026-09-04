import requests, re
from collections import Counter
s=requests.get("https://www.forwardalpha.pro/sitemap.xml",timeout=180).text
blocchi=re.findall(r"<url>(.*?)</url>", s, re.S)
print("indirizzi:",len(blocchi))
pri=Counter()
esempi={}
for b in blocchi:
    loc=re.search(r"<loc>(.*?)</loc>",b)
    p=re.search(r"<priority>(.*?)</priority>",b)
    if not p: continue
    v=p.group(1)
    pri[v]+=1
    if v not in esempi and loc and "/stock/" in loc.group(1):
        esempi[v]=loc.group(1).split("/stock/")[-1]
print()
print("=== distribuzione delle priorita' ===")
for k,v in sorted(pri.items(),reverse=True):
    print("   %-6s %5d indirizzi   esempio: %s" % (k,v,esempi.get(k,"(pagina fissa)")))
