import requests
from collections import Counter
print("=== API del sito: distribuzione delle date di prezzo restituite ===")
for eti,url in [("US","https://forwardalpha.pro/api/db/stocks?exchanges=US"),
                ("Europa","https://forwardalpha.pro/api/db/stocks?exchanges=MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,GR,LSE,SWX,OM,OB,CPSE")]:
    r=requests.get(url,timeout=90)
    d=r.json().get("stocks",[])
    c=Counter(s.get("lastPriceDate") or "SENZA DATA" for s in d)
    senza=sum(1 for s in d if s.get("price") is None)
    print("\n  %s — %d titoli restituiti" % (eti,len(d)))
    for k,v in sorted(c.items(),reverse=True)[:5]:
        print("     %-14s %4d" % (k,v))
    print("     senza prezzo: %d" % senza)

print()
print("=== ASML: la tabella ora coincide col grafico? ===")
r=requests.get("https://forwardalpha.pro/api/db/stocks?ticker=ASML&exchange=AS",timeout=60)
s=r.json().get("stocks",[{}])[0]
print("  tabella -> prezzo %s  data %s  var %s" % (s.get("price"),s.get("lastPriceDate"),s.get("change1d")))
