import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="final_full_catchup_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "final full catchup", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

def leeway_ticker(ticker):
    return ticker.rstrip(".").replace(".", "-") + ".US"

all_tickers = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_tickers.extend(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break
log(f"Universo: {len(all_tickers)}")

fresh = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1000","offset":str(offset)}, timeout=25)
    if r.status_code != 200:
        log(f"  ERRORE lettura freschi offset={offset}: HTTP {r.status_code}")
        break
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    fresh.update(row["ticker"] for row in batch)
    offset += 1000
    if len(batch) < 1000: break
log(f"Gia' freschi al 10 luglio: {len(fresh)}")

stale = [t for t in all_tickers if t not in fresh]
log(f"Da recuperare: {len(stale)}")

ok = fail = 0
buf = []
for i, ticker in enumerate(stale):
    yt = leeway_ticker(ticker)
    try:
        url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            fail += 1; continue
        data = r.json()
        if not isinstance(data, list) or not data:
            fail += 1; continue
        for row in data:
            adj = row.get("adjusted_close") or row.get("close")
            if adj is None or float(adj) >= 999999: continue
            buf.append({"ticker": ticker, "exchange": "US", "date": row["date"], "adj_close": float(adj)})
        ok += 1
    except Exception:
        fail += 1
    if len(buf) >= 300:
        resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=buf, timeout=30)
        if resp.status_code not in (200,201,204):
            log(f"  WARN batch: HTTP {resp.status_code} {resp.text[:150]}")
        buf = []
    time.sleep(0.3)
    if (i+1) % 200 == 0:
        log(f"  ...{i+1}/{len(stale)} — ok={ok} fail={fail}")
if buf:
    resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=buf, timeout=30)
    if resp.status_code not in (200,201,204):
        log(f"  WARN ultimo batch: HTTP {resp.status_code} {resp.text[:150]}")

log(f"\nFINALE: ok={ok} fail={fail} su {len(stale)} recuperati")
commit_log("\n".join(log_lines))
print("Fatto")
