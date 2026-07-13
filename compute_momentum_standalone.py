import os, requests, time, base64
from datetime import datetime, timedelta
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="compute_momentum_standalone_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "momentum standalone output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

TODAY = datetime.now()

def nearest_price(prices_by_date, target_date, tolerance_days=5):
    """Trova il prezzo alla data piu' vicina a target_date, entro tolerance_days."""
    best = None; best_diff = None
    for d, p in prices_by_date.items():
        dt = datetime.strptime(d, "%Y-%m-%d")
        diff = abs((dt - target_date).days)
        if diff <= tolerance_days and (best_diff is None or diff < best_diff):
            best = p; best_diff = diff
    return best

# Universo US
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
log(f"Universo US: {len(all_tickers)} titoli")

FROM_DATE = (TODAY - timedelta(days=400)).strftime("%Y-%m-%d")
ok = fail = 0
mom_batch = []
for i, ticker in enumerate(all_tickers):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":"eq.US",
                     "date":f"gte.{FROM_DATE}","order":"date.desc","limit":"400"}, timeout=20)
        if r.status_code != 200:
            fail += 1; continue
        rows = r.json()
        if not rows:
            fail += 1; continue
        prices_by_date = {row["date"]: row["adj_close"] for row in rows}
        latest_date = max(prices_by_date.keys())
        latest_price = prices_by_date[latest_date]
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")

        prev_date_sorted = sorted(prices_by_date.keys(), reverse=True)
        prev_price = prices_by_date[prev_date_sorted[1]] if len(prev_date_sorted) > 1 else None

        def trading_day_price(prices_by_date, n):
            # n=5 -> prezzo di 5 giorni di CONTRATTAZIONE fa (convenzione
            # Yahoo), non "n giorni di calendario piu' vicino"
            sorted_dates = sorted(prices_by_date.keys(), reverse=True)
            if len(sorted_dates) <= n: return None
            return prices_by_date[sorted_dates[n]]

        p1w = trading_day_price(prices_by_date, 5)
        p1m = nearest_price(prices_by_date, latest_dt - timedelta(days=30), 6)
        p6m = nearest_price(prices_by_date, latest_dt - timedelta(days=182), 12)
        p12m = nearest_price(prices_by_date, latest_dt - timedelta(days=365), 15)

        def pct(new, old):
            if old is None or old == 0: return None
            val = round((new/old - 1), 6)
            if abs(val) > 50: return None  # valore anomalo (probabile split/dato corrotto), scartato invece di rompere il batch
            return val

        row = {"ticker": ticker, "exchange": "US", "price": latest_price,
               "change1d": pct(latest_price, prev_price),
               "mom1w": pct(latest_price, p1w), "mom1m": pct(latest_price, p1m),
               "mom6m": pct(latest_price, p6m), "mom12m": pct(latest_price, p12m)}
        mom_batch.append(row)
        ok += 1
    except Exception as e:
        fail += 1
        if fail <= 5: log(f"  ECCEZIONE {ticker}: {e}")

    if len(mom_batch) >= 100:
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=mom_batch, timeout=30)
        if resp.status_code not in (200,201,204):
            log(f"  WARN batch: HTTP {resp.status_code} {resp.text[:200]}")
        mom_batch = []
    if (i+1) % 300 == 0:
        log(f"  ...{i+1}/{len(all_tickers)} — ok={ok} fail={fail}")

if mom_batch:
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=mom_batch, timeout=30)
    if resp.status_code not in (200,201,204):
        log(f"  WARN ultimo batch: HTTP {resp.status_code} {resp.text[:200]}")

log(f"\nFINALE: ok={ok} fail={fail} su {len(all_tickers)}")
commit_log("\n".join(log_lines))
print("Fatto")
