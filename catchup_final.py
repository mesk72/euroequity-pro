import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="catchup_final_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "catchup final output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

def leeway_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "BR": return ticker.replace(".", "") + ".BR"
    if exchange == "ASX": return ticker.rstrip(".") + ".AU"
    if exchange == "TSE": return ticker.rstrip(".") + ".TSE"
    return ticker

# ASX per intero (priorita', era rimasto indietro), poi rabbocco SEHK/BR/TSE
for exchange in ["ASX", "SEHK", "BR", "TSE"]:
    all_tickers = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{exchange}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_tickers.extend(s["ticker"] for s in batch)
        offset += 1000
        if len(batch) < 1000: break

    have_fresh = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{exchange}","date":"eq.2026-07-10","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        have_fresh.update(row["ticker"] for row in batch)
        offset += 1000
        if len(batch) < 1000: break

    stale = [t for t in all_tickers if t not in have_fresh]
    log(f"{exchange}: {len(all_tickers)} totali, {len(stale)} da recuperare")

    ok = fail = 0
    buf = []
    for i, ticker in enumerate(stale):
        yt = leeway_ticker(ticker, exchange)
        try:
            url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-09&to=2026-07-11"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                fail += 1; continue
            data = r.json()
            if not isinstance(data, list) or not data:
                fail += 1; continue
            for row in data:
                adj = row.get("adjusted_close") or row.get("close")
                if adj is None or float(adj) >= 999999: continue
                buf.append({"ticker": ticker, "exchange": exchange, "date": row["date"], "adj_close": float(adj)})
            ok += 1
        except Exception:
            fail += 1
        if len(buf) >= 300:
            resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=buf, timeout=30)
            if resp.status_code not in (200,201,204):
                log(f"  WARN batch {exchange}: HTTP {resp.status_code} {resp.text[:150]}")
            buf = []
        time.sleep(0.3)
    if buf:
        resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=buf, timeout=30)
        if resp.status_code not in (200,201,204):
            log(f"  WARN ultimo batch {exchange}: HTTP {resp.status_code} {resp.text[:150]}")
    log(f"  {exchange} FINALE: ok={ok} fail={fail}")

commit_log("\n".join(log_lines))
print("Fatto")
