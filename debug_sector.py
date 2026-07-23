import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica esatta di ey/book_yield/pct_rank usate nello script reale
def ey(pe):
    if pe is None or pe == 0: return None
    return 1.0 / pe

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb

def pct_rank(arr, val):
    if not arr or val is None: return None
    n = len(arr)
    below = sum(1 for x in arr if x < val)
    ties  = sum(1 for x in arr if x == val)
    return ((below + 0.5 * ties) / n) * 100

# Scarica un campione REALE di dati US (primi 200 per velocita')
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
             "exchange":"eq.US","limit":"300"})
all_data = r.json()
print(f"Dati scaricati: {len(all_data)}")

RANK_GROUPS = {"USA": ["US"]}

def calc_ranks(group):
    ey_trail_g = [ey(d['pe_trailing']) for d in group if ey(d['pe_trailing']) is not None]
    ey_fwd_g   = [ey(d['pe_forward'])  for d in group if ey(d['pe_forward'])  is not None]
    by_g       = [book_yield(d['pb'])   for d in group if book_yield(d['pb'])  is not None]
    eps_g_vals = [d['eps_growth']       for d in group if d['eps_growth']      is not None]
    rev_g_vals = [d['rev_growth']       for d in group if d['rev_growth']      is not None]
    mom6_adj_g = []; mom12_adj_g = []
    for d in group:
        m6, m12, m1w, m1m = d.get('mom6m'), d.get('mom12m'), d.get('mom1w'), d.get('mom1m')
        if m6 is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    pre = []
    for d in group:
        m6, m12, m1w, m1m = d.get('mom6m'), d.get('mom12m'), d.get('mom1w'), d.get('mom1m')
        ey_t = ey(d.get('pe_trailing')); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        ey_f = ey(d.get('pe_forward'));  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
        by_v = book_yield(d.get('pb'));  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
        r_epsg = pct_rank(eps_g_vals, d.get('eps_growth')) if d.get('eps_growth') is not None else None
        r_revg = pct_rank(rev_g_vals, d.get('rev_growth')) if d.get('rev_growth') is not None else None
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
    print(f"  val_sums len={len(val_sums)}, gr_sums len={len(gr_sums)}")
    results = []
    for p in pre:
        val_inputs = [x for x in [p['r_eyt'], p['r_eyf'], p['r_pb']] if x is not None]
        gr_inputs  = [x for x in [p['r_epsg'], p['r_revg'], p['r_m6'], p['r_m12']] if x is not None]
        value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs) >= 2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs) >= 3 and gr_sums  else None
        results.append({"ticker": p['ticker'], "exchange": p['exchange'],
                        "value_score": value_score, "growth_score": growth_score})
    return results

rank_updates = calc_ranks(all_data)
print(f"rank_updates: {len(rank_updates)}")
print(f"Esempio: {rank_updates[:3]}")

all_scores = [d for d in rank_updates if d.get('value_score') is not None and d.get('growth_score') is not None]
print(f"\nall_scores (con entrambi i punteggi non-null): {len(all_scores)}")
if all_scores:
    print(f"Esempio all_scores[0]: {all_scores[0]}")
else:
    # Diagnostica il perche'
    only_val = sum(1 for d in rank_updates if d.get('value_score') is not None)
    only_gr  = sum(1 for d in rank_updates if d.get('growth_score') is not None)
    print(f"DIAGNOSI: {only_val} hanno value_score, {only_gr} hanno growth_score")
