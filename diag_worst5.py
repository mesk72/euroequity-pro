import os, requests, time, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="diag_worst5_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "diag worst5", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

def leeway_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR": return ticker.replace(".", "") + ".BR"
    if exchange == "ASX": return ticker.rstrip(".") + ".AU"
    if exchange == "TSE": return ticker.rstrip(".") + ".TSE"
    return ticker

for exchange in ["TSX", "BR", "TSE", "SEHK", "ASX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{exchange}","in_universe":"eq.true","limit":"15"})
    tickers = [row["ticker"] for row in r.json()]
    log(f"\n=== {exchange}: {len(tickers)} titoli ===")
    for ticker in tickers:
        yt = leeway_ticker(ticker, exchange)
        try:
            url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{yt}?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                log(f"  {ticker} ({yt}): HTTP {r.status_code} — {r.text[:150]}")
                continue
            data = r.json()
            if not isinstance(data, list) or not data:
                log(f"  {ticker} ({yt}): risposta vuota — {data}")
                continue
            dates = sorted([row.get("date") for row in data])
            log(f"  {ticker} ({yt}): OK, date ricevute {dates}")
        except Exception as e:
            log(f"  {ticker} ({yt}): ECCEZIONE {type(e).__name__}: {e}")
        time.sleep(0.3)

commit_log("\n".join(log_lines))
print("Fatto")
