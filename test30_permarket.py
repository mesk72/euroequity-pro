import os, requests, time, base64, random
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="test30_permarket_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "test30 permarket output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)
    if len(log_lines) % 5 == 0:
        commit_log("\n".join(log_lines))  # salva progressivamente

SUFFIX = {"MIL":".MI","XETRA":".XETRA","PA":".PA","AS":".AS","LSE":".LSE","SWX":".SW",
          "OM":".ST","MC":".MC","BR":".BR","HE":".HE","CPSE":".CO","OB":".OL","GR":".AT",
          "VI":".VI","IR":".IR","LS":".LS","TSE":".TSE","ASX":".AU","KRX":".KS","SGX":".SI","TSX":".TO"}

def leeway_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "US": return ticker.rstrip(".").replace(".", "-") + ".US"
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange in ("OM","CPSE"): return ticker.replace(" ", "-") + SUFFIX.get(exchange,"")
    if exchange == "BR": return ticker.replace(".", "") + ".BR"
    return ticker.rstrip(".") + SUFFIX.get(exchange, "")

def test_market(exchange, min_date="2026-07-09"):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{exchange}","in_universe":"eq.true","limit":"500"})
    universe = [row["ticker"] for row in r.json()]
    if not universe:
        log(f"{exchange}: NESSUN TITOLO IN UNIVERSO")
        return exchange, 0, 0
    random.seed(42)
    sample = random.sample(universe, min(30, len(universe)))

    pending = list(sample)
    ok_final = set()
    for attempt in range(1, 4):
        if not pending: break
        still_pending = []
        buf = []
        for ticker in pending:
            yt = leeway_ticker(ticker, exchange)
            try:
                url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
                r = requests.get(url, timeout=15)
                if r.status_code != 200:
                    still_pending.append(ticker); continue
                data = r.json()
                if not isinstance(data, list) or not data:
                    still_pending.append(ticker); continue
                got_latest = any(row.get("date") >= min_date for row in data)
                for row in data:
                    adj = row.get("adjusted_close") or row.get("close")
                    if adj is None: continue
                    buf.append({"ticker": ticker, "exchange": exchange, "date": row["date"], "adj_close": float(adj)})
                if got_latest: ok_final.add(ticker)
                else: still_pending.append(ticker)
            except Exception:
                still_pending.append(ticker)
            time.sleep(0.25)
        if buf:
            requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date",
                headers=headers_up, json=buf, timeout=30)
        pending = still_pending
        if pending: time.sleep(4)
    log(f"{exchange}: {len(ok_final)}/{len(sample)}" + (f" — falliti: {pending}" if pending else ""))
    return exchange, len(ok_final), len(sample)

markets = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS",
           "TSE","SEHK","ASX","KRX","SGX"]

log(f"Test su {len(markets)} mercati, 30 titoli ciascuno")
all_results = []
for m in markets:
    all_results.append(test_market(m))

log("\n=== RIEPILOGO ===")
tot_ok = tot_all = 0
for ex, ok, tot in all_results:
    log(f"{ex}: {ok}/{tot}")
    tot_ok += ok; tot_all += tot
log(f"\nTOTALE: {tot_ok}/{tot_all}")

commit_log("\n".join(log_lines))
print("Fatto")
