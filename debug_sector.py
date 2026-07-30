import requests
url = "https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"
r = requests.get(url, timeout=60)
print("HTTP:", r.status_code)
print("X-Quintile-Source:", r.headers.get("X-Quintile-Source"))
print("X-Timing-Total-Ms:", r.headers.get("X-Timing-Total-Ms"))
