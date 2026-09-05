import requests, re
from collections import Counter
s=requests.get("https://www.forwardalpha.pro/sitemap.xml",timeout=180).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
prio=re.findall(r"<priority>(.*?)</priority>", s)
print("indirizzi:",len(locs),"| con priorita':",len(prio))
print()
print("=== distribuzione delle priorita' ===")
for p,n in sorted(Counter(prio).items(),reverse=True):
    print("   %-5s %5d pagine" % (p,n))
print()
print("=== priorita' di alcuni titoli noti ===")
blocchi=re.findall(r"<url>(.*?)</url>", s, re.S)
for tk in ["ASML-AS","NOVN-SWX","AAPL-US","NVDA-US","MC-PA","ICFI-US","MRTN-US"]:
    for b in blocchi:
        if "/stock/"+tk in b:
            pr=re.search(r"<priority>(.*?)</priority>",b)
            cf=re.search(r"<changefreq>(.*?)</changefreq>",b)
            print("   %-10s priorita' %-5s  %s" % (tk, pr.group(1) if pr else "-", cf.group(1) if cf else "-"))
            break
