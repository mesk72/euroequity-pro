import requests, time

url = "https://forwardalpha.pro/api/db/stocks?exchanges=US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX"

for attempt in range(2):
    t0 = time.time()
    try:
        r = requests.get(url, timeout=60)
        elapsed = time.time() - t0
        n = 0
        try:
            n = len(r.json().get("stocks", []))
        except Exception:
            pass
        print(f"Tentativo {attempt+1}: HTTP {r.status_code}, {elapsed:.2f}s, {n} titoli restituiti, {len(r.content)} bytes")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"Tentativo {attempt+1}: ERRORE dopo {elapsed:.2f}s: {e}")
