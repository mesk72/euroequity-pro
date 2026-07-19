import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Scarica TUTTI i titoli US per rifare il rank e verificare NVDA
all_rows = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,eps_growth,rev_growth,mom6m,mom1w,mom12m,mom1m","exchange":"eq.US","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_rows.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Totale titoli US: {len(all_rows)}")

def pct_rank(vals_dict):
    items = [(k,v) for k,v in vals_dict.items() if v is not None]
    n = len(items)
    if n == 0: return {}
    sorted_vals = sorted(v for k,v in items)
    out = {}
    for k, v in items:
        lower = sum(1 for x in sorted_vals if x < v)
        ties = sum(1 for x in sorted_vals if x == v)
        out[k] = round(((lower + 0.5*ties) / n) * 100, 2)
    return out

eps_vals = {r["ticker"]: r.get("eps_growth") for r in all_rows}
rev_vals = {r["ticker"]: r.get("rev_growth") for r in all_rows}
m6_vals = {r["ticker"]: (r["mom6m"]-r["mom1w"]) if r.get("mom6m") is not None and r.get("mom1w") is not None else None for r in all_rows}
m12_vals = {r["ticker"]: (r["mom12m"]-r["mom1m"]) if r.get("mom12m") is not None and r.get("mom1m") is not None else None for r in all_rows}

eps_rank = pct_rank(eps_vals)
rev_rank = pct_rank(rev_vals)
m6_rank = pct_rank(m6_vals)
m12_rank = pct_rank(m12_vals)

sums = {}
for r in all_rows:
    t = r["ticker"]
    parts = [x.get(t) for x in [eps_rank, rev_rank, m6_rank, m12_rank] if t in x]
    if len(parts) >= 3:
        sums[t] = sum(parts)

final_growth = pct_rank(sums)
print(f"\nNVDA - eps_rank: {eps_rank.get('NVDA')}, rev_rank: {rev_rank.get('NVDA')}, m6_rank: {m6_rank.get('NVDA')}, m12_rank: {m12_rank.get('NVDA')}")
print(f"NVDA - somma: {sums.get('NVDA')}")
print(f"NVDA - growth_score RICALCOLATO ORA: {final_growth.get('NVDA')}")
print(f"NVDA - growth_score SALVATO NEL DB: 90.69")
