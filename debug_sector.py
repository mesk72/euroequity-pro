import requests, time
url = "https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"
for i in range(2):
    t0 = time.time()
    r = requests.get(url, timeout=60)
    elapsed = time.time() - t0
    print(f"Tentativo {i+1}: {elapsed:.2f}s | X-Timing-Total-Ms={r.headers.get('X-Timing-Total-Ms')} | righe={r.headers.get('X-Timing-Rows')}")
