import os, requests
from collections import defaultdict

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

ALL_EXCHANGES = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS","TSE","SEHK","ASX","KRX","SGX"]
NO_RANK_EX = {"VI","LS","IR"}  # troppo pochi titoli per un rank affidabile

def pct_rank(vals_dict):
    """vals_dict: {key: value}. Ritorna {key: percentile 1-100}."""
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

print("Scarico fundamentals per tutti i mercati...", flush=True)
all_fund = []
for ex in ALL_EXCHANGES:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,eps_growth,rev_growth,mom6m,mom1w,mom12m,mom1m,value_score",
                     "exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_fund.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
print(f"Totale righe fundamentals: {len(all_fund)}", flush=True)

# STADIO 1 — Growth Score, rank per singolo exchange (proxy paese)
growth_updates = {}
by_exchange = defaultdict(list)
for row in all_fund:
    by_exchange[row["exchange"]].append(row)

for ex, rows in by_exchange.items():
    if ex in NO_RANK_EX:
        continue
    eps_vals = {r["ticker"]: r.get("eps_growth") for r in rows}
    rev_vals = {r["ticker"]: r.get("rev_growth") for r in rows}
    m6_vals = {r["ticker"]: (r["mom6m"]-r["mom1w"]) if r.get("mom6m") is not None and r.get("mom1w") is not None else None for r in rows}
    m12_vals = {r["ticker"]: (r["mom12m"]-r["mom1m"]) if r.get("mom12m") is not None and r.get("mom1m") is not None else None for r in rows}

    eps_rank = pct_rank(eps_vals)
    rev_rank = pct_rank(rev_vals)
    m6_rank = pct_rank(m6_vals)
    m12_rank = pct_rank(m12_vals)

    sums = {}
    for r in rows:
        t = r["ticker"]
        parts = [x.get(t) for x in [eps_rank, rev_rank, m6_rank, m12_rank] if t in x]
        if len(parts) >= 3:  # minimo 3 di 4 input, regola stabilita
            sums[t] = sum(parts)

    final_growth = pct_rank(sums)
    for t, g in final_growth.items():
        growth_updates[(t, ex)] = g

print(f"Growth Score calcolati: {len(growth_updates)}", flush=True)

# STADIO 2 — Best Score, combinato per CONTINENTE (non singolo exchange)
NA = ["US","TSX"]
EU = ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
APAC = ["TSE","SEHK","ASX","KRX","SGX"]
CONTINENTS = {"NA": NA, "EU": EU, "APAC": APAC}

value_by_key = {(r["ticker"], r["exchange"]): r.get("value_score") for r in all_fund}

best_updates = {}
for cname, exlist in CONTINENTS.items():
    sums = {}
    for r in all_fund:
        if r["exchange"] not in exlist: continue
        if r["exchange"] in NO_RANK_EX: continue
        key = (r["ticker"], r["exchange"])
        v = value_by_key.get(key)
        g = growth_updates.get(key)
        if v is not None and g is not None:
            sums[key] = v + g
    ranked = pct_rank(sums)
    for key, b in ranked.items():
        best_updates[key] = b

print(f"Best Score calcolati: {len(best_updates)}", flush=True)

# Scrittura
all_keys = set(growth_updates.keys()) | set(best_updates.keys())
updates = []
for (t, ex) in all_keys:
    upd = {"ticker": t, "exchange": ex}
    if (t,ex) in growth_updates: upd["growth_score"] = growth_updates[(t,ex)]
    if (t,ex) in best_updates: upd["combined_rank"] = best_updates[(t,ex)]
    updates.append(upd)

print(f"Totale da scrivere: {len(updates)}", flush=True)
ok = 0
for i in range(0, len(updates), 200):
    chunk = updates[i:i+200]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=chunk, timeout=30)
    if resp.status_code in (200,201,204): ok += len(chunk)
    else: print(f"  WARN: HTTP {resp.status_code} {resp.text[:150]}")
    if i % 2000 == 0: print(f"  Scritti finora: {ok}", flush=True)

print(f"COMPLETATO. Scritti {ok}/{len(updates)}", flush=True)
