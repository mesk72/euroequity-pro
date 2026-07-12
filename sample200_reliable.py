import os, requests, random, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="sample200_reliable_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "sample200 output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"3000"})
universe = [row["ticker"] for row in r.json()]
random.seed(1)
sample = random.sample(universe, 200)

dates = {}
stale_list = []
for t in sample:
    rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"1"})
    d = rr.json()
    dv = d[0]["date"] if d else "VUOTO"
    dates[dv] = dates.get(dv, 0) + 1
    if dv != "2026-07-10":
        stale_list.append((t, dv))

out = f"Campione affidabile di {len(sample)} titoli US:\n"
for d, c in sorted(dates.items(), reverse=True):
    out += f"  {d}: {c} ({100*c/len(sample):.1f}%)\n"
out += f"\nStima su tutto l'universo: {100*dates.get('2026-07-10',0)/len(sample):.1f}% al 10 luglio\n"
out += f"\nEsempio titoli non al 10 luglio: {stale_list[:20]}"
print(out)
commit_log(out)
