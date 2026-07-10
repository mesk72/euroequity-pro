import os, requests, time, base64
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
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(content_str.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"update {path}", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    print(f"  Commit {path}: HTTP {rp.status_code}")
    return rp.status_code in (200, 201)

# Trova chi manca ancora: universo reale meno chi e' gia' nel file fiscal_year_end.csv
import csv, io
r_fy = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r_fy.text))
have_already = set()
for row in reader:
    if row["exchange"] in ("SEHK","SGX") and row["fiscal_month"] not in ("0",""):
        have_already.add((row["ticker"], row["exchange"]))
print(f"Gia' presenti: {len(have_already)}")

to_process = []
for exch in ["SEHK","SGX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{exch}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch:
            if (s["ticker"], s["exchange"]) not in have_already:
                to_process.append(s)
        offset += 1000
        if len(batch) < 1000: break
print(f"Da recuperare (mancanti): {len(to_process)}")

rows_buffer = ["ticker,exchange,fiscal_month"]
ok_count = 0
fail = 0
for i, s in enumerate(to_process):
    ticker, exch = s["ticker"], s["exchange"]
    # Prova entrambi i formati comuni per HK (a volte serve senza zfill)
    attempts = [yahoo_ticker(ticker, exch)]
    if exch == "SEHK":
        attempts.append(ticker.lstrip("0") + ".HK")
    found = False
    for yt in attempts:
        try:
            info = yf.Ticker(yt).info
            ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
            if ts:
                month = datetime.fromtimestamp(ts, tz=timezone.utc).month
                rows_buffer.append(f"{ticker},{exch},{month}")
                ok_count += 1
                found = True
                break
        except Exception:
            continue
    if not found:
        fail += 1
    if (i+1) % 100 == 0:
        print(f"  ...{i+1}/{len(to_process)} — trovati finora {ok_count}")
        commit_to_github("\n".join(rows_buffer) + "\n", "fiscal_month_hk_sgx_gap.csv")
    time.sleep(0.2)

print(f"\nTotale trovati (gap): {ok_count}")
print(f"Ancora falliti: {fail}")
commit_to_github("\n".join(rows_buffer) + "\n", "fiscal_month_hk_sgx_gap.csv")
