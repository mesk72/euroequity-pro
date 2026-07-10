import os, requests, time, csv, base64, json
from datetime import datetime, timezone
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance")

def yahoo_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "SGX": return ticker + ".SI"
    return ticker

def commit_to_github(content_str, path):
    """Scrive direttamente su GitHub, dallo script stesso — nessun passaggio
    intermedio che possa fallire silenziosamente."""
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(content_str.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"update {path}", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    print(f"  Commit {path}: HTTP {rp.status_code}")
    return rp.status_code in (200, 201)

rows_buffer = ["ticker,exchange,fiscal_month"]
ok_count = 0
fail = 0
for exch in ["SEHK","SGX"]:
    tickers = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{exch}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        tickers.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"{exch}: {len(tickers)} titoli da processare")

    for i, s in enumerate(tickers):
        ticker = s["ticker"]
        yt = yahoo_ticker(ticker, exch)
        try:
            info = yf.Ticker(yt).info
            ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
            if ts:
                month = datetime.fromtimestamp(ts, tz=timezone.utc).month
                rows_buffer.append(f"{ticker},{exch},{month}")
                ok_count += 1
            else:
                fail += 1
        except Exception:
            fail += 1
        if (i+1) % 150 == 0:
            print(f"  ...{i+1}/{len(tickers)} — trovati finora {ok_count}")
            # Commit intermedio ogni 150 titoli, cosi' il progresso e' salvato
            # anche se il resto dello script si interrompe
            commit_to_github("\n".join(rows_buffer) + "\n", "fiscal_month_hk_sgx.csv")
        time.sleep(0.2)

print(f"\nTotale trovati: {ok_count}")
print(f"Falliti: {fail}")
final_ok = commit_to_github("\n".join(rows_buffer) + "\n", "fiscal_month_hk_sgx.csv")
print(f"Commit finale riuscito: {final_ok}")
