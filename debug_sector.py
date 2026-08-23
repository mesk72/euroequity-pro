import requests
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1)"}
print("=== quale dominio serve davvero? ===")
for u in ["https://www.forwardalpha.pro/stock/AAPL-US",
          "https://www.forwardalpha.pro/",
          "https://forwardalpha.pro/stock/AAPL-US"]:
    r=requests.get(u,timeout=60,headers=UA,allow_redirects=False)
    print("  %-46s HTTP %s %s" % (u[:46],r.status_code,r.headers.get("location","")[:50]))
print()
print("=== seguendo i reindirizzamenti ===")
r=requests.get("https://forwardalpha.pro/stock/AAPL-US",timeout=60,headers=UA)
print("  finale:",r.url,"HTTP",r.status_code,"| lunghezza:",len(r.text))
print()
print("=== il canonical della pagina che punta a cosa? ===")
import re
m=re.search(r'<link rel="canonical" href="([^"]+)"',r.text)
print("  canonical:", m.group(1) if m else "ASSENTE")
print()
print("=== robots.txt ===")
rb=requests.get("https://forwardalpha.pro/robots.txt",timeout=30)
print(rb.text[:400])
