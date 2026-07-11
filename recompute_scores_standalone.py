import os, requests, base64

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="recompute_scores_standalone_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "recompute scores output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

def ey(pe):
    try:
        pe = float(pe)
        return 1.0/pe if pe != 0 else None
    except Exception:
        return None

def book_yield(pb):
    try:
        pb = float(pb)
        return 100 - (100*pb) if False else None  # placeholder, sostituito sotto correttamente
    except Exception:
        return None

# book_yield reale: 100 - pct_rank(pb) va applicato dopo — qui serve solo un valore
# invertito coerente con "piu' basso e' meglio": usiamo -pb come proxy per il rank
def book_yield(pb):
    try:
        return -float(pb)
    except Exception:
        return None

def pct_rank(arr, val):
    if val is None or not arr: return None
    arr_sorted = sorted(arr)
    n = len(arr_sorted)
    below = sum(1 for x in arr_sorted if x < val)
    return 100 * below / n if n > 0 else None

# Leggi TUTTI i fundamentals US con il momentum ORA corretto
all_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom1w,mom1m,mom6m,mom12m",
                "exchange":"eq.US","limit":"1000","offset":str(offset)}, timeout=30)
    data = r.json()
    if not isinstance(data, list) or not data: break
    all_data.extend(data)
    offset += 1000
    if len(data) < 1000: break
log(f"Fundamentals US letti: {len(all_data)}")

ey_trail_g = [ey(d['pe_trailing']) for d in all_data if ey(d['pe_trailing']) is not None]
ey_fwd_g   = [ey(d['pe_forward'])  for d in all_data if ey(d['pe_forward'])  is not None]
by_g       = [book_yield(d['pb'])  for d in all_data if book_yield(d['pb']) is not None]
eps_g_vals = [d['eps_growth']      for d in all_data if d['eps_growth']     is not None]
rev_g_vals = [d['rev_growth']      for d in all_data if d['rev_growth']     is not None]
mom6_adj_g = []; mom12_adj_g = []
for d in all_data:
    m6, m1w, m12, m1m = d.get('mom6m'), d.get('mom1w'), d.get('mom12m'), d.get('mom1m')
    if m6 is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
    if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)

pre = []
for d in all_data:
    ey_t = ey(d.get('pe_trailing')); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
    ey_f = ey(d.get('pe_forward'));  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
    by_v = book_yield(d.get('pb'));  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
    r_epsg = pct_rank(eps_g_vals, d.get('eps_growth')) if d.get('eps_growth') is not None else None
    r_revg = pct_rank(rev_g_vals, d.get('rev_growth')) if d.get('rev_growth') is not None else None
    m6, m1w, m12, m1m = d.get('mom6m'), d.get('mom1w'), d.get('mom12m'), d.get('mom1m')
    mom6_adj  = (m6 - m1w) if m6 is not None and m1w is not None else None
    mom12_adj = (m12 - m1m) if m12 is not None and m1m is not None else None
    r_m6  = pct_rank(mom6_adj_g,  mom6_adj)  if mom6_adj  is not None else None
    r_m12 = pct_rank(mom12_adj_g, mom12_adj) if mom12_adj is not None else None
    pre.append({"ticker": d['ticker'], "exchange": d['exchange'],
                "r_eyt": r_eyt, "r_eyf": r_eyf, "r_pb": r_pb,
                "r_epsg": r_epsg, "r_revg": r_revg, "r_m6": r_m6, "r_m12": r_m12})

val_sums = [sum(x for x in [p['r_eyt'], p['r_eyf'], p['r_pb']] if x is not None)
            for p in pre if len([x for x in [p['r_eyt'], p['r_eyf'], p['r_pb']] if x is not None]) >= 2]
gr_sums  = [sum(x for x in [p['r_epsg'], p['r_revg'], p['r_m6'], p['r_m12']] if x is not None)
            for p in pre if len([x for x in [p['r_epsg'], p['r_revg'], p['r_m6'], p['r_m12']] if x is not None]) >= 3]

results = []
for p in pre:
    val_inputs = [x for x in [p['r_eyt'], p['r_eyf'], p['r_pb']] if x is not None]
    gr_inputs  = [x for x in [p['r_epsg'], p['r_revg'], p['r_m6'], p['r_m12']] if x is not None]
    value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs) >= 2 and val_sums else None
    growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs) >= 3 and gr_sums  else None
    results.append({"ticker": p['ticker'], "exchange": p['exchange'],
                    "value_score": value_score, "growth_score": growth_score,
                    "rank_pe_ltm": round(p['r_eyt']) if p['r_eyt'] is not None else None,
                    "rank_pe_ntm": round(p['r_eyf']) if p['r_eyf'] is not None else None,
                    "rank_pb": round(p['r_pb']) if p['r_pb'] is not None else None,
                    "rank_eps_gr": round(p['r_epsg']) if p['r_epsg'] is not None else None,
                    "rank_rev_gr": round(p['r_revg']) if p['r_revg'] is not None else None,
                    "rank_mom6_adj": round(p['r_m6']) if p['r_m6'] is not None else None,
                    "rank_mom12_adj": round(p['r_m12']) if p['r_m12'] is not None else None})

# combined_rank
scored = [r for r in results if r['value_score'] is not None and r['growth_score'] is not None]
comb_arr = [r['value_score'] + r['growth_score'] for r in scored]
for r in results:
    if r['value_score'] is not None and r['growth_score'] is not None:
        r['combined_rank'] = min(99, round(pct_rank(comb_arr, r['value_score'] + r['growth_score'])))
    else:
        r['combined_rank'] = None

log(f"Titoli rankati: {len(results)}")

# Scrittura BATCH (non piu' un PATCH per titolo)
ok = 0; fail = 0
for i in range(0, len(results), 200):
    batch = results[i:i+200]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=batch, timeout=30)
    if resp.status_code in (200, 201, 204):
        ok += len(batch)
    else:
        fail += len(batch)
        log(f"  WARN batch {i}: HTTP {resp.status_code} {resp.text[:200]}")

log(f"\nFINALE: scritti ok={ok} fail={fail} su {len(results)}")
commit_log("\n".join(log_lines))
print("Fatto")
