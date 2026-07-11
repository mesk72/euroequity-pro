import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="test30_all_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "test30 output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

def leeway_ticker(ticker, exchange):
    suffix = {"MIL":".MI","XETRA":".XETRA","PA":".PA","AS":".AS","LSE":".LSE","SWX":".SW",
              "TSE":".TSE","SEHK":None,"ASX":".AU","KRX":".KS","SGX":".SI"}
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "US": return ticker.rstrip(".").replace(".", "-") + ".US"
    return ticker.rstrip(".") + suffix.get(exchange, "")

def test_region(label, exchanges, today="2026-07-11"):
    all_tickers = []
    for ex in exchanges:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"200"})
        all_tickers.extend([(row["ticker"], row["exchange"]) for row in r.json()])
    import random
    random.seed(42)
    sample = random.sample(all_tickers, min(30, len(all_tickers)))

    log(f"\n=== {label}: campione di {len(sample)} titoli ===")
    pending = list(sample)
    ok_final = set()
    for attempt in range(1, 5):  # fino a 4 tentativi per garantire convergenza reale
        if not pending: break
        log(f"  Tentativo {attempt}: {len(pending)} da processare")
        still_pending = []
        buf = []
        for ticker, exchange in pending:
            yt = leeway_ticker(ticker, exchange)
            try:
                url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
                r = requests.get(url, timeout=15)
                if r.status_code != 200:
                    still_pending.append((ticker, exchange))
                    continue
                data = r.json()
                if not isinstance(data, list) or not data:
                    still_pending.append((ticker, exchange))
                    continue
                got_latest = any(row.get("date") >= "2026-07-09" for row in data)
                for row in data:
                    adj = row.get("adjusted_close") or row.get("close")
                    if adj is None: continue
                    buf.append({"ticker": ticker, "exchange": exchange, "date": row["date"], "adj_close": float(adj)})
                if got_latest:
                    ok_final.add((ticker, exchange))
                else:
                    still_pending.append((ticker, exchange))
            except Exception:
                still_pending.append((ticker, exchange))
            time.sleep(0.3)
        if buf:
            resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date",
                headers=headers_up, json=buf, timeout=30)
            if resp.status_code not in (200,201,204):
                log(f"    WARN scrittura: HTTP {resp.status_code} {resp.text[:200]}")
        pending = still_pending
        if pending:
            time.sleep(5)
    log(f"  RISULTATO {label}: {len(ok_final)}/{len(sample)}")
    if pending:
        log(f"  Ancora falliti dopo 4 tentativi: {pending}")
    return len(ok_final), len(sample)

results = {}
results["US"] = test_region("US", ["US"])
results["EU"] = test_region("EU", ["MIL","XETRA","PA","LSE","AS"])
results["APAC"] = test_region("APAC", ["TSE","SEHK","ASX","KRX","SGX"])

log("\n=== RIEPILOGO FINALE ===")
for label, (ok, tot) in results.items():
    log(f"{label}: {ok}/{tot}")

commit_log("\n".join(log_lines))
print("Fatto")
