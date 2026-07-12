import os, requests, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="count_exact_july10_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "count exact", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

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

at_10 = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-10","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    at_10.update(row["ticker"] for row in batch)
    offset += 1000
    if len(batch) < 1000: break

missing = sorted(set(all_tickers) - at_10)
out = f"Universo: {len(all_tickers)}\nAl 10 luglio: {len(at_10)}\nMancanti: {len(missing)}\nEsempio: {missing[:30]}"
print(out)
commit_log(out)
