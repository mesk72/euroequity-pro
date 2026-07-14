import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def pct_rank(arr, val):
    below = sum(1 for x in arr if x < val)
    return round(below / len(arr) * 100)

# ── Input noti ──
price_drop = 0.18
eps_ltm_cut = 0.35
eps_ntm_cut = 0.32
rev_gr_rank_cut = 0.15  # riduzione esplicita del rank, non del valore

old = {
    "eps_ltm": 0.4144, "eps_ntm": 0.3847,
    "mom6m": 1.5235, "mom12m": 0.9238,
    "rank_pe_ltm": 57, "rank_pe_ntm": 50, "rank_pb": 97,  # gia' calcolati prima
    "rank_rev_gr": 77,
}

# EPS growth (approccio NTM/LTM diretto, assunzione dichiarata)
new_eps_ltm = old["eps_ltm"] * (1 - eps_ltm_cut)
new_eps_ntm = old["eps_ntm"] * (1 - eps_ntm_cut)
new_eps_growth = new_eps_ntm/abs(new_eps_ltm) - 1

# Momentum: il calo prezzo tocca anche mom6m/mom12m (che includono il prezzo di oggi)
new_mom6m  = (old["mom6m"]+1)  * (1-price_drop) - 1
new_mom12m = (old["mom12m"]+1) * (1-price_drop) - 1
new_mom1w  = -price_drop   # il calo e' concentrato in un giorno recente
new_mom1m  = -price_drop
new_mom6_adj  = new_mom6m  - new_mom1w
new_mom12_adj = new_mom12m - new_mom1m

print(f"Nuovo EPS growth: {new_eps_growth*100:.2f}%")
print(f"Nuovo mom6_adj: {new_mom6_adj:.4f}  |  Nuovo mom12_adj: {new_mom12_adj:.4f}")

# ── Distribuzioni reali Norvegia per i rank ──
universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.OB","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break

eps_g_vals, m6adj_vals, m12adj_vals = [], [], []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,eps_growth,rank_mom6_adj,rank_mom12_adj,mom6m,mom12m,mom1w,mom1m","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe:
            if d.get("eps_growth") is not None:
                eps_g_vals.append(d["eps_growth"])
            m6 = d.get("mom6m"); m1w = d.get("mom1w")
            if m6 is not None and m1w is not None:
                m6adj_vals.append(m6 - m1w)
            m12 = d.get("mom12m"); m1m = d.get("mom1m")
            if m12 is not None and m1m is not None:
                m12adj_vals.append(m12 - m1m)
    offset += 1000
    if len(batch) < 1000: break

new_rank_eps_gr = pct_rank(eps_g_vals, new_eps_growth)
new_rank_mom6_adj = pct_rank(m6adj_vals, new_mom6_adj)
new_rank_mom12_adj = pct_rank(m12adj_vals, new_mom12_adj)
new_rank_rev_gr = round(old["rank_rev_gr"] * (1 - rev_gr_rank_cut))

print(f"\nrank_eps_gr: {new_rank_eps_gr} (prima: 85)")
print(f"rank_rev_gr: {new_rank_rev_gr} (prima: 77, ridotto -15% come richiesto)")
print(f"rank_mom6_adj: {new_rank_mom6_adj} (prima: 99)")
print(f"rank_mom12_adj: {new_rank_mom12_adj} (prima: 93)")

# ── Value Score (EU o Norvegia? uso Norvegia per coerenza coi PE gia' calcolati) ──
val_sums = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,pe_trailing,pe_forward,pb","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    def ey(pe):
        if pe is None or pe==0 or abs(pe)>200: return None
        return 1/pe
    def by(pb):
        if pb is None or pb==0: return None
        return 1/pb
    ey_l = [ey(d["pe_trailing"]) for d in batch if ey(d["pe_trailing"]) is not None]
    ey_f = [ey(d["pe_forward"]) for d in batch if ey(d["pe_forward"]) is not None]
    b_g  = [by(d["pb"]) for d in batch if by(d["pb"]) is not None]
    for d in batch:
        if d["ticker"] in universe:
            rl = pct_rank(ey_l, ey(d["pe_trailing"])) if ey(d["pe_trailing"]) is not None else None
            rf = pct_rank(ey_f, ey(d["pe_forward"])) if ey(d["pe_forward"]) is not None else None
            rb = pct_rank(b_g, by(d["pb"])) if by(d["pb"]) is not None else None
            inputs = [x for x in [rl,rf,rb] if x is not None]
            if len(inputs) >= 2:
                val_sums.append(sum(inputs))
    offset += 1000
    if len(batch) < 1000: break

new_val_sum = old["rank_pe_ltm"] + old["rank_pe_ntm"] + old["rank_pb"]
new_value_score = pct_rank(val_sums, new_val_sum)
print(f"\nNUOVO VALUE SCORE (Norvegia): {new_value_score} (prima: 85)")

gr_sum = new_rank_eps_gr + new_rank_rev_gr + new_rank_mom6_adj + new_rank_mom12_adj
gr_sums_all = []
# approssimazione: uso somma dei 4 rank su tutto il gruppo Norvegia per il secondo stadio
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,rank_eps_gr,rank_rev_gr,rank_mom6_adj,rank_mom12_adj","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe:
            vals = [d.get("rank_eps_gr"), d.get("rank_rev_gr"), d.get("rank_mom6_adj"), d.get("rank_mom12_adj")]
            valid = [v for v in vals if v is not None]
            if len(valid) >= 3:
                gr_sums_all.append(sum(valid))
    offset += 1000
    if len(batch) < 1000: break

new_growth_score = pct_rank(gr_sums_all, gr_sum)
print(f"NUOVO GROWTH SCORE (Norvegia): {new_growth_score} (prima: 95)")

# ── Best Score su EU intera ──
EU_EXCHANGES = ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS']
all_eu_sums = []
for ex in EU_EXCHANGES:
    u2 = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        u2.update(s["ticker"] for s in batch)
        offset += 1000
        if len(batch) < 1000: break
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,value_score,growth_score","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch:
            if d["ticker"] in u2 and d.get("value_score") is not None and d.get("growth_score") is not None:
                all_eu_sums.append(d["value_score"]+d["growth_score"])
        offset += 1000
        if len(batch) < 1000: break

new_best_sum = new_value_score + new_growth_score
new_best_score = min(99, pct_rank(all_eu_sums, new_best_sum))
print(f"\nNUOVO BEST SCORE (EU intera): {new_best_score} (prima: 99)")
