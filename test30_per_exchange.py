import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SERVICE_KEY", "") or os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="test30_per_exchange_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "test30 per exchange output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

EXCHANGES = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","LS","VI","HE","IR","GR","OB","CPSE",
             "TSE","SEHK","ASX","KRX","SGX"]

results = {}
for ex in EXCHANGES:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"30"})
    tickers = [row["ticker"] for row in r.json()] if r.status_code == 200 else []
    if not tickers:
        log(f"{ex}: NESSUN TITOLO in_universe trovato")
        continue
    dates = {}
    for t in tickers:
        rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
        d = rr.json()
        date_val = d[0]["date"] if d else "VUOTO"
        dates[date_val] = dates.get(date_val, 0) + 1
    freshest = max(dates.keys()) if dates else "N/A"
    freshest_count = dates.get(freshest, 0)
    log(f"{ex}: campione {len(tickers)} — piu' recente: {freshest} ({freshest_count}/{len(tickers)}) — distribuzione: {dates}")
    results[ex] = (freshest_count, len(tickers), freshest)
    time.sleep(0.2)

log("\n=== RIEPILOGO ===")
for ex, (ok, tot, fr) in results.items():
    mark = "OK" if ok == tot else "PROBLEMA"
    log(f"{ex}: {ok}/{tot} alla data piu' recente ({fr}) — {mark}")

commit_log("\n".join(log_lines))
print("Fatto")
