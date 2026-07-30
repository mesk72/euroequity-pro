import requests, time
url = "https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"
t0 = time.time()
r = requests.get(url, timeout=90, headers={"Accept-Encoding": "gzip, br"}, stream=True)
ttfb = time.time() - t0
content = r.content
total = time.time() - t0
print(f"TTFB (primo byte): {ttfb:.2f}s | tempo totale download: {total:.2f}s")
print(f"Content-Encoding: {r.headers.get('content-encoding')}")
print(f"Content-Length dichiarato: {r.headers.get('content-length')}")
print(f"Byte scaricati (dopo eventuale decompressione): {len(content)} ({len(content)/1024/1024:.2f} MB)")
print(f"Righe: {r.headers.get('X-Timing-Rows')}, tempo server: {r.headers.get('X-Timing-Total-Ms')}ms")
# stima per proprietario: 7889 righe invece di 500
n_rows = int(r.headers.get('X-Timing-Rows', 500))
if n_rows > 0:
    stima_owner_mb = len(content) / n_rows * 7889 / 1024 / 1024
    print(f"Stima dimensione risposta per proprietario (7889 righe, no filtro): {stima_owner_mb:.1f} MB")
