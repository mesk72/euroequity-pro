import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1)"}
print("=== TITOLO E DESCRIZIONE della homepage (cio' che Google mostra) ===")
r=requests.get("https://www.forwardalpha.pro/",timeout=60,headers=UA)
t=re.search(r"<title>(.*?)</title>",r.text,re.S)
d=re.search(r'<meta name="description" content="(.*?)"',r.text,re.S)
print("  titolo:     ",(t.group(1) if t else "-"))
print("  descrizione:",(d.group(1) if d else "-")[:200])
print()
print("=== quanti indirizzi ha la sitemap e di che tipo ===")
s=requests.get("https://www.forwardalpha.pro/sitemap.xml",timeout=120).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
print("  totale:",len(locs))
stock=[l for l in locs if "/stock/" in l]
print("  schede titolo:",len(stock))
print()
print("=== esempi di schede titolo nella sitemap: sono titoli importanti? ===")
import random
for l in stock[:6]+stock[-6:]: print("   ",l.replace("https://www.forwardalpha.pro/stock/",""))
