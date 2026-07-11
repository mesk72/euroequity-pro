import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json"}

def commit_log(text, path="test100_v2_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "test100 output", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    return rp.status_code

def leeway_ticker(ticker):
    return ticker.rstrip(".").replace(".", "-") + ".US"

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"100"})
tickers = [row["ticker"] for row in r.json()]
log(f"Test su {len(tickers)} titoli reali")

status_counts = {}
fail_detail = []
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
            fail_detail.append(f"{ticker} ({yt}): HTTP {r.status_code} - {r.text[:150]}")
            continue
        data = r.json()
        if not isinstance(data, list) or not data:
            fail += 1
            fail_detail.append(f"{ticker} ({yt}): risposta vuota - {data}")
            continue
        got_july10 = any(row.get("date") == "2026-07-10" for row in data)
        if not got_july10:
            fail += 1
            fail_detail.append(f"{ticker} ({yt}): OK ma senza 10 luglio - date ricevute: {[row.get('date') for row in data]}")
            # scriviamo comunque quello che c'e'
        for row in data:
            adj = row.get("adjusted_close") or row.get("close")
            if adj is None: continue
            price_buf.append({"ticker": ticker, "exchange": "US", "date": row["date"], "adj_close": float(adj)})
        if got_july10:
            ok += 1
    except Exception as e:
        fail += 1
        fail_detail.append(f"{ticker} ({yt}): ECCEZIONE {type(e).__name__}: {e}")
    time.sleep(0.3)
    if (i+1) % 25 == 0:
        log(f"  ...{i+1}/100 processati")

elapsed = time.time() - t0
log(f"\nFetch completato in {elapsed:.1f}s")
log(f"OK con dato al 10 luglio: {ok}")
log(f"FALLITI o senza 10 luglio: {fail}")
log(f"Distribuzione HTTP: {status_counts}")
log(f"\nDettaglio primi 20 falliti:")
for d in fail_detail[:20]:
    log(f"  {d}")

if price_buf:
    resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers={**headers_up, "Prefer":"resolution=merge-duplicates,return=minimal"}, json=price_buf, timeout=30)
    log(f"\nScrittura {len(price_buf)} righe: HTTP {resp.status_code}")
    if resp.status_code not in (200,201,204):
        log(f"  ERRORE SCRITTURA: {resp.text[:500]}")

log("\n=== FINE TEST ===")
commit_status = commit_log("\n".join(log_lines))
print(f"Commit log: HTTP {commit_status}")
