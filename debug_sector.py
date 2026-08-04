import requests, json
print("=== Il sito ora mostra prezzi coerenti col grafico? ===")
# ASML: in prices_eod l'ultima seduta e' il 3/8 a 1419.60
r=requests.get("https://forwardalpha.pro/api/db/stocks?ticker=ASML&exchange=AS",timeout=60)
d=r.json()
s=(d.get("stocks") or [{}])[0]
print("\nAPI scheda titolo ASML:")
print("   price      :",s.get("price"))
print("   change1d   :",s.get("change1d"))
print("   lastPriceDate:",s.get("lastPriceDate"))
print("   (in prices_eod: 2026-08-03 = 1419.60)")

print("\n=== Quanti titoli ricevono ora il prezzo? (mercato grande) ===")
r2=requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=US",timeout=90)
d2=r2.json().get("stocks",[])
con=sum(1 for x in d2 if x.get("price") is not None)
senza=len(d2)-con
from collections import Counter
date=Counter(x.get("lastPriceDate") for x in d2 if x.get("lastPriceDate"))
print("   titoli restituiti:",len(d2))
print("   con prezzo       :",con)
print("   senza prezzo     :",senza)
print("   date presenti    :",dict(date.most_common(4)))
