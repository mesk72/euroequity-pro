import requests
print("Screener (percorso BULK) vs scheda titolo (percorso SINGOLO) — ASML")
b=requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=AS",timeout=60).json()
tro=[x for x in b.get("stocks",[]) if x.get("ticker")=="ASML"]
print("  screener :", (tro[0].get("price"), tro[0].get("lastPriceDate")) if tro else "non presente")
s=requests.get("https://forwardalpha.pro/api/db/stocks?ticker=ASML&exchange=AS",timeout=45).json()
ss=(s.get("stocks") or [{}])[0]
print("  scheda   :", (ss.get("price"), ss.get("lastPriceDate")))
