# ============================================================
# FORWARDALPHA — WEEKLY EU LOAD
# Da eseguire ogni domenica alle 08:00 CET
# REGOLE: FORWARDALPHA_CONTEXT.md
# - calendarizzazione dinamica con fy_end.year
# - book_yield = 1/pb (PB negativi inclusi)
# - PE negativi inclusi sempre
# - Portugal (LS) in NO_RANK
# ============================================================

import csv, requests, math, os, io, time as time_module
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY        = datetime.now().strftime("%Y-%m-%d")
TODAY_DT     = datetime.now()

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","DB":"XETRA","DUSE":"XETRA",
    "MUN":"XETRA","BRSE":"BR","HMSE":"OM","XSAT":"OM","OTCNO":"OB",
}

RANK_GROUPS = {
    "ITA": ["MIL"], "DEU": ["XETRA"], "FRA": ["PA"], "GBR": ["LSE"],
    "SWE": ["OM"],  "NOR": ["OB"],    "CHE": ["SWX"], "NLD": ["AS"],
    "BEL": ["BR"],  "FIN": ["HE"],    "ESP": ["MC"],  "DNK": ["CPSE"],
}
NO_RANK = {"AT", "VI", "IR", "NGM", "AIM", "LS"}  # Portugal escluso

def parse_num(v):
    if v is None: return None
    try:
        import pandas as pd
        if pd.isna(v): return None
    except: pass
    s = str(v).strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True; s = s[1:-1]
    # Rimuovi suffissi non numerici
    s = s.replace('$','').replace('x','').replace('%','').strip()
    # Rimuovi suffissi tipo USDMM, MM ecc.
    for suf in ['USDMM','EURMM','MM','B','bn']:
        s = s.replace(suf,'').strip()
    if s in ['-','','N/A','nm',chr(8212)]: return None
    # Gestisci formato europeo: punto=migliaia, virgola=decimale
    # es. "691.603,06" -> 691603.06, "9,99" -> 9.99
    if ',' in s and '.' in s:
        # Formato con entrambi: punto migliaia, virgola decimale
        s = s.replace('.','').replace(',','.')
    elif ',' in s:
        # Solo virgola: potrebbe essere decimale europeo
        # Se c'e' solo una virgola e max 2 cifre dopo -> decimale
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',','.')
        else:
            s = s.replace(',','')
    try:
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None

def pct_rank(values, v):
    if v is None: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    valid = [x for x in values if x is not None]
    if not valid: return None
    below = sum(1 for x in valid if x < v)
    return max(1, min(99, int(round(below / len(valid) * 100))))

def ey(pe):
    if pe is None or pe == 0: return None
    return 1.0 / pe  # PE negativi inclusi sempre

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb  # PB negativi inclusi

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA WEEKLY EU LOAD — {TODAY}")
print("=" * 60)

# ── FISCAL YEAR END ──────────────────────────────────────────
print("\n Legge fiscal year end...")
fy_map = {}
try:
    r_fy = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_fy.text))
    for row in reader:
        ticker   = row["ticker"].strip()
        exchange = row["exchange"].strip()
        month    = parse_num(row.get("fiscal_month", "12"))
        fy_map[(ticker, exchange)] = int(month) if month else 12
    print(f" FY end caricati: {len(fy_map)}")
except Exception as e:
    print(f" FY end non trovato, uso dicembre default: {e}")

def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)

def calendarize(ticker, exchange, fy2025, fy2026, fy2027, fy2028, today_dt):
    """Calendarizzazione DINAMICA — mai hardcoded"""
    if fy2025 is None and fy2026 is None: return None, None, True
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm == 2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year - 1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        return None, None, True  # not_yet → usa fy2027/fy2028
    # Determina fy0/fy1/fy2 dinamicamente da fy_end.year
    if fy_end.year >= 2026:
        v0, v1, v2 = fy2026, fy2027, fy2028
    else:
        v0, v1, v2 = fy2025, fy2026, fy2027
    next_pub = datetime(pub_date.year + 1, pub_date.month, pub_date.day)
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next
    ltm = w_curr * v0 + w_next * v1 if v0 is not None and v1 is not None else None
    ntm = w_curr * v1 + w_next * v2 if v1 is not None and v2 is not None else None
    return ltm, ntm, False

# ── TIKR EU ──────────────────────────────────────────────────
print("\n Legge file TIKR EU...")
tikr_rows = []
try:
    r_tikr = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_tikr.text))
    for row in reader:
        ticker   = row["Ticker"].strip()
        exchange = EX_MAP.get(row["Primary Exchange"].strip(), row["Primary Exchange"].strip())
        if not ticker or not exchange: continue
        tikr_rows.append({
            "ticker": ticker, "exchange": exchange,
            "company": row["Company Name"].strip(),
            "pe_trailing": parse_num(row.get("LTM P/E LTM","")),
            "pe_forward":  parse_num(row.get("Mean Fwd P/E NTM","")),
            "pb":          parse_num(row.get("LTM P/BVPS LTM","")),
            "eps_fy0": parse_num(row.get("EPS Normalized (FY 2025)","")),
            "eps_fy1": parse_num(row.get("Mean EPS Normalized (FY 2026)","")),
            "eps_fy2": parse_num(row.get("Mean EPS Normalized (FY 2027)","")),
            "eps_fy3": parse_num(row.get("Mean EPS Normalized (FY 2028)","")),
            "eps_fy4": parse_num(row.get("Mean EPS (GAAP) (FY 2029)","") or row.get("Mean EPS Normalized (FY 2029)","")),
            "eps_fy5": parse_num(row.get("Mean EPS Normalized (FY 2030)","") or row.get("Mean EPS (GAAP) (FY 2030)","")),
            "rev_fy0": parse_num(row.get("Rev (FY 2025)","")),
            "rev_fy1": parse_num(row.get("Mean Rev (FY 2026)","")),
            "rev_fy2": parse_num(row.get("Mean Rev (FY 2027)","")),
            "rev_fy3": parse_num(row.get("Mean Rev (FY 2028)","")),
        })
    print(f" TIKR EU: {len(tikr_rows)} titoli")
except Exception as e:
    print(f" Errore lettura TIKR: {e}"); exit()

# ── CARICA UNIVERSE KEYS DA STOCKS ───────────────────────────
universe_keys = set()
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","in_universe":"eq.true",
                "exchange":"not.in.(US,TSX,TSE,SEHK,ASX,KRX,SGX)",
                "offset":str(offset),"limit":"1000"})
    batch = res.json()
    if not isinstance(batch, list) or not batch: break
    for s in batch: universe_keys.add((s["ticker"],s["exchange"]))
    offset += 1000
    if len(batch) < 1000: break
print(f" Universe EU: {len(universe_keys)}")

# Filtra tikr_rows solo per titoli in universe
tikr_rows = [r for r in tikr_rows if (r["ticker"],r["exchange"]) in universe_keys]
print(f" TIKR EU in universe: {len(tikr_rows)}")

# ── FONDAMENTALI + CALENDARIZZAZIONE ─────────────────────────
print("\n Calcola fondamentali...")
fund_updates = []
for r in tikr_rows:
    ticker   = r["ticker"]
    exchange = r["exchange"]
    eps_ltm, eps_ntm, not_yet = calendarize(
        ticker, exchange,
        r["eps_fy0"], r["eps_fy1"], r["eps_fy2"], r["eps_fy3"], TODAY_DT)
    rev_ltm, rev_ntm, _ = calendarize(
        ticker, exchange,
        r["rev_fy0"], r["rev_fy1"], r["rev_fy2"], r["rev_fy3"], TODAY_DT)
    if not_yet:
        eps_growth = (r["eps_fy3"]/abs(r["eps_fy2"])-1) if r["eps_fy3"] and r["eps_fy2"] and r["eps_fy2"]!=0 else None
        rev_growth = (r["rev_fy3"]/r["rev_fy2"]-1)     if r["rev_fy3"] and r["rev_fy2"] and r["rev_fy2"]!=0 else None
    else:
        eps_growth = (eps_ntm/abs(eps_ltm)-1) if eps_ntm and eps_ltm and eps_ltm!=0 else None
        rev_growth = (rev_ntm/abs(rev_ltm)-1) if rev_ntm and rev_ltm and rev_ltm!=0 else None
    fund_updates.append({
        "ticker": ticker, "exchange": exchange,
        "pe_trailing": round(r["pe_trailing"],2) if r["pe_trailing"] is not None else None,
        "pe_forward":  round(r["pe_forward"],2)  if r["pe_forward"]  is not None else None,
        "pb": r["pb"],
        "eps_fy0": r["eps_fy0"], "eps_fy1": r["eps_fy1"],
        "eps_fy2": r["eps_fy2"], "eps_fy3": r["eps_fy3"],
        "eps_fy4": r.get("eps_fy4"),
        "eps_fy5": r.get("eps_fy5"),
        "eps_growth": round(eps_growth,6) if eps_growth is not None else None,
        "rev_growth": round(rev_growth,6) if rev_growth is not None else None,
    })
ok = 0
for i in range(0, len(fund_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=fund_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(fund_updates[i:i+100])
    elif i == 0:
        print(f" ERRORE HTTP {r.status_code}: {r.text[:200]}")
print(f" Fondamentali: {ok}/{len(fund_updates)}")

# ── MOMENTUM DAL DB ──────────────────────────────────────────
print("\n Legge rank momentum dal DB...")
mom_rank_map = {}
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,rank_mom6_adj,rank_mom12_adj",
                "exchange":"not.in.(US,TSX,TSE,SEHK,ASX)","in_universe":"eq.true",
                "offset":str(offset),"limit":"1000"})
    data = res.json()
    if not isinstance(data, list) or not data: break
    for d in data:
        mom_rank_map[(d["ticker"],d["exchange"])] = {
            "r_m6": d.get("rank_mom6_adj"), "r_m12": d.get("rank_mom12_adj")}
    offset += 1000
    if len(data) < 1000: break
print(f" Momentum: {len(mom_rank_map)}")

# ── LEGGE FONDAMENTALI AGGIORNATI ───────────────────────────
# Usa direttamente fund_updates (già filtrati per in_universe)
all_data = []
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth",
                "exchange":"not.in.(US,TSX,TSE,SEHK,ASX,KRX,SGX)",
                "offset":str(offset),"limit":"1000"})
    batch = res.json()
    if not isinstance(batch, list) or not batch: break
    all_data.extend([d for d in batch if (d["ticker"],d["exchange"]) in universe_keys])
    offset += 1000
    if len(batch) < 1000: break
print(f" Fondamentali DB: {len(all_data)}")

# ── RANK ─────────────────────────────────────────────────────
def calc_ranks(group):
    ey_trail_g = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g   = [ey(d["pe_forward"])  for d in group if ey(d["pe_forward"])  is not None]
    by_g       = [book_yield(d["pb"])   for d in group if book_yield(d["pb"])  is not None]
    eps_g_vals = [d["eps_growth"] for d in group if d["eps_growth"] is not None]
    rev_g_vals = [d["rev_growth"] for d in group if d["rev_growth"] is not None]
    pre = []
    for d in group:
        key  = (d["ticker"], d["exchange"])
        ey_t = ey(d["pe_trailing"]); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        ey_f = ey(d["pe_forward"]);  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
        by_v = book_yield(d["pb"]);  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
        r_epsg = pct_rank(eps_g_vals, d["eps_growth"]) if d["eps_growth"] is not None else None
        r_revg = pct_rank(rev_g_vals, d["rev_growth"]) if d["rev_growth"] is not None else None
        mom   = mom_rank_map.get(key, {})
        r_m6  = mom.get("r_m6"); r_m12 = mom.get("r_m12")
        pre.append({"ticker":d["ticker"],"exchange":d["exchange"],
                    "r_eyt":r_eyt,"r_eyf":r_eyf,"r_pb":r_pb,
                    "r_epsg":r_epsg,"r_revg":r_revg,"r_m6":r_m6,"r_m12":r_m12})
    val_sums = [sum(x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None)
                for p in pre if len([x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None])>=2]
    gr_sums  = [sum(x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None)
                for p in pre if len([x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None])>=2]
    results = []
    for p in pre:
        val_inputs = [x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None]
        gr_inputs  = [x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None]
        value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs)>=2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs)>=2 and gr_sums  else None
        results.append({"ticker":p["ticker"],"exchange":p["exchange"],
                        "value_score":value_score,"growth_score":growth_score,
                        "rank_pe_ltm":p["r_eyt"],"rank_pe_ntm":p["r_eyf"],"rank_pb":p["r_pb"],
                        "rank_eps_gr":p["r_epsg"],"rank_rev_gr":p["r_revg"]})
    return results

rank_updates = []
for country, exchanges in RANK_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f" {country}: {len(res)}")

ranked_exchanges = set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked = [d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked: rank_updates.extend(calc_ranks(unranked))

# Salva copia rank_updates con ticker/exchange per il combined
rank_updates_copy = [dict(upd) for upd in rank_updates]
ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print(f" Rank EU: {ok}/{len(rank_updates)}")

# ── COMBINED EU ──────────────────────────────────────────────
# Debug
has_vs = sum(1 for d in rank_updates_copy if d.get("value_score") is not None)
has_gs = sum(1 for d in rank_updates_copy if d.get("growth_score") is not None)
print(f" rank_updates_copy: {len(rank_updates_copy)} titoli, con value_score={has_vs} con growth_score={has_gs}")
all_scores = [d for d in rank_updates_copy if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates = [{"ticker":d["ticker"],"exchange":d["exchange"],
                     "combined_rank":min(99,pct_rank(sum_arr,d["value_score"]+d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print(f" Combined EU: {ok}/{len(combined_updates)}")

end_time = time_module.time()
print(f"\nWeekly EU completato in {int(end_time-start_time)}s")
print("=" * 60)
