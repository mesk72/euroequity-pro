import requests
b=requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=AS",timeout=60).json()
t=[x for x in b.get("stocks",[]) if x.get("ticker")=="ASML"]
print("  screener:", (t[0].get("price"), t[0].get("lastPriceDate")) if t else "assente")
s=requests.get("https://forwardalpha.pro/api/db/stocks?ticker=ASML&exchange=AS",timeout=45).json()
ss=(s.get("stocks") or [{}])[0]
print("  scheda  :", (ss.get("price"), ss.get("lastPriceDate")))
