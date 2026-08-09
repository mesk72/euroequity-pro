import requests, re
s=requests.get("https://forwardalpha.pro/sitemap.xml",timeout=90).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("Indirizzi nella sitemap: %d" % len(locs))
tipi={}
for l in locs:
    p=l.replace("https://forwardalpha.pro","").strip("/").split("/")
    k=p[0] if p and p[0] else "(home)"
    tipi[k]=tipi.get(k,0)+1
for k,v in sorted(tipi.items(),key=lambda x:-x[1]):
    print("   %-12s %d" % (k,v))
print()
print("Esempi di schede titolo incluse:")
for l in [x for x in locs if "/stock/" in x][:6]: print("   ",l)
print()
print("Ci sono ancora indirizzi /screens rotti?", any("/screens" in x for x in locs))
