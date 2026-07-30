import requests, time

tests = [
    ("stocks (dati titolo) - AAPL", "https://forwardalpha.pro/api/db/stocks?ticker=AAPL&exchange=US"),
    ("history (grafico) - AAPL", "https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=1825"),
    ("stocks (dati titolo) - ASML", "https://forwardalpha.pro/api/db/stocks?ticker=ASML&exchange=AS"),
    ("history (grafico) - ASML", "https://forwardalpha.pro/api/db/history?ticker=ASML&exchange=AS&days=1825"),
]
for label, url in tests:
    t0 = time.time()
    try:
        r = requests.get(url, timeout=30)
        elapsed = time.time() - t0
        print(f"{label}: {elapsed:.2f}s | HTTP {r.status_code} | {len(r.content)} byte")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"{label}: ERRORE dopo {elapsed:.2f}s: {e}")
