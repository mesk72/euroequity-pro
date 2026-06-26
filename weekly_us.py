# ============================================================
# FORWARDALPHA — WEEKLY US+CA LOAD
# Da eseguire ogni domenica alle 08:00 CET
# REGOLE: FORWARDALPHA_CONTEXT.md
# - universo: US + TSX (Canada)
# - calendarizzazione dinamica con fy_end.year
# - book_yield = 1/pb (PB negativi inclusi)
# - combined NA = US+TSX insieme
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
    s = s.replace('$','').replace(',','').replace('x','').replace('%','').strip()
    if s in ['-','','N/A','nm',chr(8212)]: return None
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
    return 1.0 / pe

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA WEEKLY US+CA LOAD — {TODAY}")
print("=" * 60)

# ── FISCAL YEAR END ──────────────────────────────────────────
print("\n Legge fiscal year end...")
fy_map = {}
try:
    r_fy = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/fiscal_year_end.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_fy.text))
    for row in reader:
        ticker   = row["ticker"].strip()
        exchange = row["exchange"].strip()
        month    = parse_num(row.get("fiscal_month","12"))
        fy_map[(ticker, exchange)] = int(month) if month else 12
    print(f" FY end: {len(fy_map)}")
except Exception as e:
    print(f" FY end non trovato: {e}")

def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)

def calendarize(ticker, exchange, fy2025, fy2026, fy2027, fy2028, today_dt):
    """Calendarizzazione DINAMICA"""
    if fy2025 is None and fy2026 is None: return None, None, True
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm==2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year-1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        return None, None, True
    if fy_end.year >= 2026:
        v0, v1, v2 = fy2026, fy2027, fy2028
    else:
        v0, v1, v2 = fy2025, fy2026, fy2027
    next_pub = datetime(pub_date.year+1, pub_date.month, pub_date.day)
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next
    ltm = w_curr*v0 + w_next*v1 if v0 is not None and v1 is not None else None
    ntm = w_curr*v1 + w_next*v2 if v1 is not None and v2 is not None else None
    return ltm, ntm, False

# ── TIKR US ──────────────────────────────────────────────────
print("\n Legge file TIKR US...")
tikr_rows = []
try:
    r_tikr = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/tikr_us_latest.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_tikr.text))
    for row in reader:
        ticker = row["Ticker"].strip()
        if not ticker: continue
        tikr_rows.append({
            "ticker": ticker, "exchange": "US",
            "pe_trailing": parse_num(row.get("Trailing P/Diluted EPS before Extra LTM","")),
            "pe_forward":  parse_num(row.get("Mean Forward P/E NTM","")),
            "pb":          parse_num(row.get("Trailing P/BVPS LTM","")),
            "eps_fy0": parse_num(row.get("EPS Normalized (FY 2025)","")),
            "eps_fy1": parse_num(row.get("Mean EPS Normalized (FY 2026)","")),
            "eps_fy2": parse_num(row.get("Mean EPS Normalized (FY 2027)","")),
            "eps_fy3": parse_num(row.get("Mean EPS Normalized (FY 2028)","")),
            "rev_fy0": parse_num(row.get("Revenue (FY 2025)","")),
            "rev_fy1": parse_num(row.get("Mean Revenue (FY 2026)","")),
            "rev_fy2": parse_num(row.get("Mean Revenue (FY 2027)","")),
            "rev_fy3": parse_num(row.get("Mean Revenue (FY 2028)","")),
        })
    print(f" TIKR US: {len(tikr_rows)}")
except Exception as e:
    print(f" Errore TIKR US: {e}"); exit()

# ── TIKR CANADA ──────────────────────────────────────────────
print("\n Legge file TIKR Canada...")
try:
    r_ca = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/tikr_ca_latest.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_ca.text))
    ca_count = 0
    for row in reader:
        ticker = row["Ticker"].strip()
        if not ticker: continue
        tikr_rows.append({
            "ticker": ticker, "exchange": "TSX",
            "pe_trailing": parse_num(row.get("Trailing P/Diluted EPS before Extra LTM","")),
            "pe_forward":  parse_num(row.get("Mean Forward P/E NTM","")),
            "pb":          parse_num(row.get("Trailing P/BVPS LTM","")),
            "eps_fy0": parse_num(row.get("EPS Normalized (FY 2025)","")),
            "eps_fy1": parse_num(row.get("Mean EPS Normalized (FY 2026)","")),
            "eps_fy2": parse_num(row.get("Mean EPS Normalized (FY 2027)","")),
            "eps_fy3": parse_num(row.get("Mean EPS Normalized (FY 2028)","")),
            "rev_fy0": parse_num(row.get("Revenue (FY 2025)","")),
            "rev_fy1": parse_num(row.get("Mean Revenue (FY 2026)","")),
            "rev_fy2": parse_num(row.get("Mean Revenue (FY 2027)","")),
            "rev_fy3": parse_num(row.get("Mean Revenue (FY 2028)","")),
        })
        ca_count += 1
    print(f" TIKR CA: {ca_count}")
except Exception as e:
    print(f" TIKR CA non trovato (continua solo US): {e}")

print(f" Totale US+CA: {len(tikr_rows)}")

# ── FONDAMENTALI ─────────────────────────────────────────────
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
        "eps_growth": round(eps_growth,6) if eps_growth is not None else None,
        "rev_growth": round(rev_growth,6) if rev_growth is not None else None,
    })
ok = 0
for i in range(0, len(fund_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_up, json=fund_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(fund_updates[i:i+100])
print(f" Fondamentali: {ok}/{len(fund_updates)}")

# ── MOMENTUM DAL DB (US+TSX) ─────────────────────────────────
mom_rank_map = {}
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,rank_mom6_adj,rank_mom12_adj",
                "exchange":"in.(US,TSX)","in_universe":"eq.true",
                "offset":str(offset),"limit":"1000"})
    data = res.json()
    if not data: break
    for d in data:
        mom_rank_map[(d["ticker"],d["exchange"])] = {
            "r_m6": d.get("rank_mom6_adj"), "r_m12": d.get("rank_mom12_adj")}
    offset += 1000
    if len(data) < 1000: break
print(f" Momentum: {len(mom_rank_map)}")

# ── FONDAMENTALI DB ──────────────────────────────────────────
all_data = []
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth",
                "exchange":"in.(US,TSX)","in_universe":"eq.true",
                "offset":str(offset),"limit":"1000"})
    data = res.json()
    if not data: break
    all_data.extend(data); offset += 1000
    if len(data) < 1000: break
print(f" Fondamentali DB: {len(all_data)}")

# ── RANK US e CA separati ────────────────────────────────────
RANK_GROUPS = {"USA": ["US"], "CAN": ["TSX"]}

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
                for p in pre if len([x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None])>=3]
    results = []
    for p in pre:
        val_inputs = [x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None]
        gr_inputs  = [x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None]
        value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs)>=2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs)>=3 and gr_sums  else None
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

ok = 0
for i in range(0, len(rank_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(rank_updates[i:i+100])
print(f" Rank US+CA: {ok}/{len(rank_updates)}")

# ── COMBINED NA = US+TSX ─────────────────────────────────────
# combined_rank NON azzerato — aggiorna direttamente con merge-duplicates
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
comb_arr   = [d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates = [{"ticker":d["ticker"],"exchange":d["exchange"],
                     "combined_rank":min(99,pct_rank(comb_arr,d["value_score"]+d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(combined_updates[i:i+100])
print(f" Combined NA (US+TSX): {ok}/{len(combined_updates)}")

end_time = time_module.time()
print(f"\nWeekly US+CA completato in {int(end_time-start_time)}s")
print("=" * 60)
