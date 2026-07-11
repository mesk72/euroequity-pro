import os, requests, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="count_july10_v3_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "count july10 v3", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

universe = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.extend(row["ticker"] for row in batch)
    offset += 1000
    if len(batch) < 1000: break

at10 = 0
dates_seen = {}
for i, t in enumerate(universe):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"1"}, timeout=10)
    d = r.json()
    dv = d[0]["date"] if d else "VUOTO"
    dates_seen[dv] = dates_seen.get(dv, 0) + 1
    if dv == "2026-07-10":
        at10 += 1
    if (i+1) % 500 == 0:
        commit_log(f"...{i+1}/{len(universe)} — al 10 luglio finora: {at10}")

result = f"Universo US: {len(universe)}\nAl 10 luglio: {at10}\nDistribuzione completa: {dates_seen}"
print(result)
commit_log(result)
