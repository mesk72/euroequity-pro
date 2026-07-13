import os, requests, csv, io, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="find_all_collisions_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "collisions output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
text = r.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))

by_ticker = {}
for row in reader:
    t = row.get('Ticker','').strip().upper()
    if not t: continue
    by_ticker.setdefault(t, []).append(row)

collisions = {t: rows for t, rows in by_ticker.items() if len(rows) > 1}
out = f"Ticker totali nel file: {len(by_ticker)}\nTicker duplicati (US+Canada stesso simbolo): {len(collisions)}\n\n"
for t, rows in sorted(collisions.items()):
    out += f"{t}:\n"
    for row in rows:
        out += f"  {row.get('Primary Exchange')} | {row.get('Country')} | {row.get('Company Name')} | MktCap={row.get('Last Mkt Cap')}\n"
print(out)
commit_log(out)
