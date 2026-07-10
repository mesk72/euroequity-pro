import os, requests, time, base64, csv, io
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

def commit_to_github(content_str, path):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(content_str.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"update {path}", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    print(f"  Commit {path}: HTTP {rp.status_code}")

us_universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    us_universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break

r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
have = set(row["ticker"] for row in reader if row["exchange"] == "US")
missing = sorted(us_universe - have)
print(f"Da recuperare: {len(missing)}")

rows_buffer = ["ticker,exchange,fiscal_month"]
ok = fail = 0
for i, ticker in enumerate(missing):
    yt = ticker.replace(".", "-")
    try:
        info = yf.Ticker(yt).info
        ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
        if ts:
            month = datetime.fromtimestamp(ts, tz=timezone.utc).month
            rows_buffer.append(f"{ticker},US,{month}")
            ok += 1
        else:
            fail += 1
    except Exception:
        fail += 1
    time.sleep(0.2)

print(f"Trovati: {ok}  Falliti: {fail}")
commit_to_github("\n".join(rows_buffer) + "\n", "fiscal_month_us_gap.csv")
