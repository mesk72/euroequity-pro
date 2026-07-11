import os, requests, time, base64
from datetime import datetime, timedelta
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="fix_68_missing_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "fix68 output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

MISSING = ['AAOI', 'AIR', 'ALHC', 'AORT', 'BLND', 'BOC', 'CCSI', 'CGEM', 'CODI', 'CPAY', 'CTOS', 'CUBI', 'CXII', 'CXM', 'DBCA', 'DCTH', 'DDI', 'DPC', 'DRTS', 'ECVT', 'ELA', 'EVER', 'EVEX', 'FBRX', 'FISV', 'FRPH', 'GDRX', 'GENI', 'GPRE', 'HKD', 'HONA', 'HRTG', 'HYLN', 'IBEX', 'IBRX', 'IHRT', 'IMMX', 'INDI', 'INDV', 'KARD', 'KEYY', 'KRAQ', 'LINC', 'LOT', 'MBGL', 'MLTX', 'MTUS', 'MTW', 'NB', 'NPKI', 'ODD', 'OLMA', 'OPFI', 'PATH', 'PNTG', 'QBTS', 'REAX', 'RZLV', 'SCSC', 'SRAD', 'STTK', 'VLNT', 'VTEX', 'WOLF', 'WOOF', 'XMTR', 'XPRO', 'YSWY']

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

TODAY = datetime.now()
FROM_DATE = (TODAY - timedelta(days=400)).strftime("%Y-%m-%d")

def nearest_price(prices_by_date, target_date, tolerance_days):
    best = None; best_diff = None
    for d, p in prices_by_date.items():
        dt = datetime.strptime(d, "%Y-%m-%d")
        diff = abs((dt - target_date).days)
        if diff <= tolerance_days and (best_diff is None or diff < best_diff):
            best = p; best_diff = diff
    return best

ok = fail = 0
mom_batch = []
for ticker in MISSING:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":"eq.US",
                     "date":f"gte.{FROM_DATE}","order":"date.desc","limit":"400"}, timeout=20)
        rows = r.json()
        if not rows:
            log(f"{ticker}: NESSUN PREZZO in prices_eod per gli ultimi 400 giorni — dato mancante a monte, non un bug di calcolo")
            fail += 1
            continue
        prices_by_date = {row["date"]: row["adj_close"] for row in rows}
        latest_date = max(prices_by_date.keys())
        latest_price = prices_by_date[latest_date]
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
        log(f"{ticker}: {len(rows)} righe, piu' recente {latest_date}={latest_price}")

        prev_sorted = sorted(prices_by_date.keys(), reverse=True)
        prev_price = prices_by_date[prev_sorted[1]] if len(prev_sorted) > 1 else None
        p1w = nearest_price(prices_by_date, latest_dt - timedelta(days=7), 5)
        p1m = nearest_price(prices_by_date, latest_dt - timedelta(days=31), 8)
        p6m = nearest_price(prices_by_date, latest_dt - timedelta(days=182), 15)
        p12m = nearest_price(prices_by_date, latest_dt - timedelta(days=365), 20)

        def pct(new, old):
            if old is None or old == 0: return None
            val = round((new/old - 1), 6)
            if abs(val) > 50: return None
            return val

        row = {"ticker": ticker, "exchange": "US", "price": latest_price,
               "change1d": pct(latest_price, prev_price),
               "mom1w": pct(latest_price, p1w), "mom1m": pct(latest_price, p1m),
               "mom6m": pct(latest_price, p6m), "mom12m": pct(latest_price, p12m)}
        mom_batch.append(row)
        ok += 1
    except Exception as e:
        fail += 1
        log(f"{ticker}: ECCEZIONE {type(e).__name__}: {e}")
    time.sleep(0.3)

if mom_batch:
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=mom_batch, timeout=30)
    log(f"\nScrittura {len(mom_batch)} righe: HTTP {resp.status_code}")
    if resp.status_code not in (200,201,204):
        log(f"  ERRORE: {resp.text[:500]}")

log(f"\nFINALE: ok={ok} fail={fail} su {len(MISSING)}")
commit_log("\n".join(log_lines))
print("Fatto")
