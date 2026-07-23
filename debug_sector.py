import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
             "exchange":"eq.TSX","limit":"1000"})
group = r.json()
print(f"Dati TSX scaricati: {len(group)}")

try:
    ey_trail_g = [ey(d['pe_trailing']) for d in group if ey(d['pe_trailing']) is not None]
    ey_fwd_g   = [ey(d['pe_forward'])  for d in group if ey(d['pe_forward'])  is not None]
    by_g       = [book_yield(d['pb'])   for d in group if book_yield(d['pb'])  is not None]
    eps_g_vals = [d['eps_growth']       for d in group if d['eps_growth']      is not None]
    rev_g_vals = [d['rev_growth']       for d in group if d['rev_growth']      is not None]
    print("Liste base costruite OK")
    mom6_adj_g = []; mom12_adj_g = []
    for d in group:
        m6, m12, m1w, m1m = d.get('mom6m'), d.get('mom12m'), d.get('mom1w'), d.get('mom1m')
        if m6 is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    print(f"mom6_adj_g={len(mom6_adj_g)}, mom12_adj_g={len(mom12_adj_g)}")
    print("TUTTO OK, nessuna eccezione")
except Exception as e:
    import traceback
    print(f"ECCEZIONE TROVATA: {e}")
    traceback.print_exc()
