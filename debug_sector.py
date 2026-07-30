import requests, time

tests = [
    ("US soltanto (3002 titoli)", "US"),
    ("US+TSX (3402 titoli)", "US,TSX"),
    ("EU completa (2137 titoli)", "MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,GR,LSE,SWX,OM,OB,CPSE"),
    ("Global (7889 titoli, 23 exchange)", "US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"),
]

for label, exch in tests:
    url = f"https://forwardalpha.pro/api/db/stocks?exchanges={exch}"
    t0 = time.time()
    r = requests.get(url, timeout=90)
    elapsed = time.time() - t0
    print(f"{label}: {elapsed:.2f}s totali | X-Timing-Total-Ms={r.headers.get('X-Timing-Total-Ms')} | righe={r.headers.get('X-Timing-Rows')}")
