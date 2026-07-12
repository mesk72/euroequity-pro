import os, requests, random, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit_log(text, path="stats_and_intc_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "stats and intc", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

def sample_freshness(label, exchanges, n=200):
    universe = []
    for ex in exchanges:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"3000"})
        universe.extend([(row["ticker"], row["exchange"]) for row in r.json()])
    random.seed(42)
    sample = random.sample(universe, min(n, len(universe)))
    fresh = 0
    dates = {}
    for t, ex in sample:
        rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
        d = rr.json()
        dv = d[0]["date"] if d else "VUOTO"
        dates[dv] = dates.get(dv, 0) + 1
        if dv == "2026-07-10": fresh += 1
    log(f"\n{label}: universo totale {len(universe)}, campione {len(sample)}")
    log(f"  Al 10 luglio: {fresh}/{len(sample)} = {100*fresh/len(sample):.1f}%")
    log(f"  Stima su tutto l'universo: ~{int(len(universe)*fresh/len(sample))}/{len(universe)}")
    for d, c in sorted(dates.items(), reverse=True):
        log(f"    {d}: {c}")

sample_freshness("NORTH AMERICA (US+TSX)", ["US","TSX"])
sample_freshness("ALL EUROPE", ["MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS"])

# INTC deep check
log("\n=== INTC ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.INTC","exchange":"eq.US"})
d = r.json()[0]
for k in ["price","change1d","mom1w","mom1m","mom6m","mom12m","value_score","growth_score","combined_rank",
          "rank_eps_gr","rank_rev_gr","rank_mom6_adj","rank_mom12_adj","eps_growth","rev_growth"]:
    log(f"  {k}: {d.get(k)}")

mom12_adj = (d.get("mom12m") or 0) - (d.get("mom1m") or 0)
mom6_adj = (d.get("mom6m") or 0) - (d.get("mom1w") or 0)
log(f"  CALCOLO mom12_adj = mom12m - mom1m = {d.get('mom12m')} - {d.get('mom1m')} = {mom12_adj}")
log(f"  CALCOLO mom6_adj  = mom6m - mom1w  = {d.get('mom6m')} - {d.get('mom1w')} = {mom6_adj}")

commit_log("\n".join(log_lines))
print("Fatto")
