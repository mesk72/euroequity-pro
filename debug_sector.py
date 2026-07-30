import requests, time
url = "https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"
t0 = time.time()
r = requests.get(url, timeout=60)
elapsed = time.time() - t0
print(f"HTTP {r.status_code}, {elapsed:.2f}s totali (rete+server)")
print("X-Timing-Total-Ms:", r.headers.get("X-Timing-Total-Ms"))
print("X-Timing-Rows:", r.headers.get("X-Timing-Rows"))
