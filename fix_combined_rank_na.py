import os, requests, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="fix_combined_rank_na_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "fix combined rank na output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

def pct_rank(arr, val):
    if val is None or not arr: return None
    below = sum(1 for x in arr if x < val)
    return int(round(below / len(arr) * 100))

# Ricombina US + TSX insieme per il Best Score, come fa daily_us.py.
# Necessario perche' lo script TSX di stanotte aveva ricalcolato
# combined_rank solo sul Canada da solo, rompendo la combinazione.
NA_EXCHANGES = ['US', 'TSX']

all_data = []
for ex in NA_EXCHANGES:
    universe = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)}, timeout=30)
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        universe.update(s["ticker"] for s in batch)
        offset += 1000
        if len(batch) < 1000: break

    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,value_score,growth_score","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)}, timeout=30)
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch:
            if d["ticker"] in universe and d.get("value_score") is not None and d.get("growth_score") is not None:
                all_data.append(d)
        offset += 1000
        if len(batch) < 1000: break

log(f"Titoli NA (US+TSX) con value+growth score: {len(all_data)}")
comb_arr = [d["value_score"] + d["growth_score"] for d in all_data]
updates = [{"ticker": d["ticker"], "exchange": d["exchange"],
            "combined_rank": min(99, pct_rank(comb_arr, d["value_score"] + d["growth_score"]))}
           for d in all_data]

ok = fail = 0
for i in range(0, len(updates), 200):
    batch = updates[i:i+200]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=batch, timeout=30)
    if resp.status_code in (200,201,204):
        ok += len(batch)
    else:
        fail += len(batch)
        log(f"  WARN: HTTP {resp.status_code} {resp.text[:200]}")

log(f"\nFINALE: ok={ok} fail={fail}")
commit_log("\n".join(log_lines))
print("Fatto")
