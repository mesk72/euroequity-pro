import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json"}

def leeway_ticker(ticker):
    return ticker.rstrip(".").replace(".", "-") + ".US"

# 100 ticker campione dall'universo US
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"100"})
tickers = [row["ticker"] for row in r.json()]
print(f"Test su {len(tickers)} titoli")

status_counts = {}
ok = fail = 0
price_buf = []
t0 = time.time()
for i, ticker in enumerate(tickers):
    yt = leeway_ticker(ticker)
    try:
        url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
        r = requests.get(url, timeout=15)
        status_counts[r.status_code] = status_counts.get(r.status_code, 0) + 1
        if r.status_code != 200:
            fail += 1
            if fail <= 10:
                print(f"  FALLITO {ticker} ({yt}): HTTP {r.status_code} — {r.text[:150]}")
            continue
        data = r.json()
        if not isinstance(data, list) or not data:
            fail += 1
            if fail <= 10:
                print(f"  FALLITO {ticker} ({yt}): risposta vuota/non lista: {data}")
            continue
        for row in data:
            adj = row.get("adjusted_close") or row.get("close")
            if adj is None: continue
            price_buf.append({"ticker": ticker, "exchange": "US", "date": row["date"], "adj_close": float(adj)})
        ok += 1
    except Exception as e:
        fail += 1
        if fail <= 10:
            print(f"  ECCEZIONE {ticker}: {type(e).__name__}: {e}")
    time.sleep(0.3)

elapsed = time.time() - t0
print(f"\nFetch completato in {elapsed:.1f}s — ok={ok} fail={fail}")
print(f"Distribuzione HTTP: {status_counts}")

if price_buf:
    resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf, timeout=30)
    print(f"Scrittura {len(price_buf)} righe: HTTP {resp.status_code}")
    if resp.status_code not in (200,201,204):
        print(f"  ERRORE: {resp.text[:300]}")
