# ============================================================
# FORWARDALPHA — WEEKLY EU LOAD
# Da eseguire ogni domenica alle 08:00 CET
# ============================================================

import csv, requests, math, os, io, time as time_module
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_DT = datetime.now()

headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","ATSE":"GR","DB":"XETRA",
    "DUSE":"XETRA","MUN":"XETRA","BRSE":"BR","HMSE":"OM",
    "XSAT":"OM","OTCNO":"OB"
}

RANK_GROUPS = {
    "ITA":["MIL"],"DEU":["XETRA"],"FRA":["PA"],"GBR":["LSE"],
    "SWE":["OM"],"NOR":["OB"],"CHE":["SWX"],"NLD":["AS"],
    "BEL":["BR"],"FIN":["HE"],"ESP":["MC"],"DNK":["CPSE"],
    "POR":["LS"],"GRE":["GR"]
}
NO_RANK = {"AT","VI","IR","NGM","AIM"}

def parse_num(v):
    if not v or str(v).strip() in ("","−","-","N/A","NM","nan"): return None
    try:
        return float(str(v).replace(",","").replace("$","").replace("%","").replace("x","").strip())
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
    try:
        if math.isnan(float(pe)): return None
    except: return None
    return 1.0 / pe

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA WEEKLY EU LOAD — {TODAY}")
print("=" * 60)

# ── LEGGE FILE FISCAL YEAR END DA SUPABASE STORAGE ──────────
print("\n Legge fiscal year end...")
fy_map = {}
try:
    r_fy = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/fiscal_year_end.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_fy.text))
    for row in reader:
        ticker = row["ticker"].strip()
        exchange = row["exchange"].strip()
        month = parse_num(row.get("fiscal_month","12"))
        fy_map[(ticker, exchange)] = int(month) if month else 12
    print(f" FY end caricati: {len(fy_map)}")
except Exception as e:
    print(f" FY end non trovato, uso dicembre default: {e}")

def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)

def calendarize(ticker, exchange, fy0, fy1, fy2, fy3, today_dt):
    if fy0 is None and fy1 is None: return None, None, True
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm==2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year-1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    next_pub = datetime(pub_date.year+1, pub_date.month, pub_date.day)
    if pub_date > today_dt:
        return None, None, True
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next
    ltm = w_curr*fy0 + w_next*fy1 if fy0 is not None and fy1 is not None else None
    ntm = w_curr*fy1 + w_next*fy2 if fy1 is not None and fy2 is not None else None
    return ltm, ntm, False

# ── LEGGE FILE TIKR EU DA SUPABASE STORAGE ──────────────────
print("\n Legge file TIKR EU...")
tikr_rows = []
try:
    r_tikr = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/public/tikr-uploads/tikr_eu_latest.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_tikr.text))
    for row in reader:
        ticker = row["Ticker"].strip()
        exchange = EX_MAP.get(row["Primary Exchange"].strip(), row["Primary Exchange"].strip())
        if not ticker or not exchange: continue
        tikr_rows.append({
            "ticker": ticker, "exchange": exchange,
            "company": row["Company Name"].strip(),
            "pe_trailing": parse_num(row.get("Trailing P/Diluted EPS before Extra LTM","")),
            "pe_forward": parse_num(row.get("Mean Forward P/E NTM","")),
            "pb": parse_num(row.get("Trailing P/BVPS LTM","")),
            "eps_fy0": parse_num(row.get("EPS Normalized (FY 2025)","")),
            "eps_fy1": parse_num(row.get("Mean EPS Normalized (FY 2026)","")),
            "eps_fy2": parse_num(row.get("Mean EPS Normalized (FY 2027)","")),
            "eps_fy3": parse_num(row.get("Mean EPS Normalized (FY 2028)","")),
            "rev_fy0": parse_num(row.get("Revenue (FY 2025)","")),
            "rev_fy1": parse_num(row.get("Mean Revenue (FY 2026)","")),
            "rev_fy2": parse_num(row.get("Mean Revenue (FY 2027)","")),
            "rev_fy3": parse_num(row.get("Mean Revenue (FY 2028)","")),
        })
    print(f" TIKR EU: {len(tikr_rows)} titoli")
except Exception as e:
    print(f" Errore lettura TIKR: {e}")
    exit()

# ── CALCOLA FONDAMENTALI ─────────────────────────────────────
print("\n Calcola fondamentali...")
fund_updates = []

for r in tikr_rows:
    ticker = r["ticker"]
    exchange = r["exchange"]

    eps_ltm, eps_ntm, not_yet = calendarize(
        ticker, exchange,
        r["eps_fy0"], r["eps_fy1"], r["eps_fy2"], r["eps_fy3"], TODAY_DT)
    rev_ltm, rev_ntm, _ = calendarize(
        ticker, exchange,
        r["rev_fy0"], r["rev_fy1"], r["rev_fy2"], r["rev_fy3"], TODAY_DT)

    if not_yet:
        eps_growth = (r["eps_fy3"]/abs(r["eps_fy2"])-1) if r["eps_fy3"] and r["eps_fy2"] and r["eps_fy2"]!=0 else None
        rev_growth = (r["rev_fy3"]/r["rev_fy2"]-1) if r["rev_fy3"] and r["rev_fy2"] and r["rev_fy2"]!=0 else None
    else:
        eps_growth = (eps_ntm/abs(eps_ltm)-1) if eps_ntm and eps_ltm and eps_ltm!=0 else None
        rev_growth = (rev_ntm/abs(rev_ltm)-1) if rev_ntm and rev_ltm and rev_ltm!=0 else None

    fund_updates.append({
        "ticker": ticker, "exchange": exchange,
        "pe_trailing": round(r["pe_trailing"],2) if r["pe_trailing"] else None,
        "pe_forward": round(r["pe_forward"],2) if r["pe_forward"] else None,
        "pb": r["pb"],
        "eps_fy0": r["eps_fy0"], "eps_fy1": r["eps_fy1"],
        "eps_fy2": r["eps_fy2"], "eps_fy3": r["eps_fy3"],
        "eps_growth": round(eps_growth,6) if eps_growth is not None else None,
        "rev_growth": round(rev_growth,6) if rev_growth is not None else None,
    })

ok = 0
for i in range(0, len(fund_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=fund_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(fund_updates[i:i+100])
print(f" Fondamentali aggiornati: {ok}/{len(fund_updates)}")

# ── LEGGE RANK MOMENTUM (congelati dal daily) ────────────────
print("\n Legge rank momentum dal DB...")
mom_rank_map = {}
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,rank_mom6_adj,rank_mom12_adj",
                "exchange":"not.eq.US","offset":str(offset),"limit":"1000"})
    data = res.json()
    if not data: break
    for d in data:
        mom_rank_map[(d["ticker"],d["exchange"])] = {
            "r_m6": d.get("rank_mom6_adj"),
            "r_m12": d.get("rank_mom12_adj")
        }
    offset += 1000
    if len(data) < 1000: break
print(f" Momentum rank caricati: {len(mom_rank_map)}")

# ── LEGGE FONDAMENTALI AGGIORNATI ───────────────────────────
print("\n Legge fondamentali aggiornati...")
all_data = []
offset = 0
while True:
    res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth",
                "exchange":"not.eq.US","offset":str(offset),"limit":"1000"})
    data = res.json()
    if not data: break
    all_data.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f" Fondamentali: {len(all_data)} titoli")

# ── CALCOLA RANK ─────────────────────────────────────────────
print("\n Calcola rank Value/Growth/Best...")

def calc_ranks(group):
    ey_trail_g = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g = [ey(d["pe_forward"]) for d in group if ey(d["pe_forward"]) is not None]
    pb_g = [d["pb"] for d in group if d["pb"] is not None and not math.isnan(float(d["pb"]))]
    eps_g_vals = [d["eps_growth"] for d in group if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
    rev_g_vals = [d["rev_growth"] for d in group if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]

    pre = []
    for d in group:
        key = (d["ticker"], d["exchange"])
        ey_t = ey(d["pe_trailing"])
        ey_f = ey(d["pe_forward"])
        pb_v = d.get("pb")
        eps_g = d.get("eps_growth")
        rev_g = d.get("rev_growth")
        r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        r_eyf = pct_rank(ey_fwd_g, ey_f) if ey_f is not None else None
        r_pb = pct_rank([1/x for x in pb_g if x!=0], 1/pb_v if pb_v and pb_v!=0 else None) if pb_v and pb_v!=0 else None
        r_epsg = pct_rank(eps_g_vals, eps_g) if eps_g is not None else None
        r_revg = pct_rank(rev_g_vals, rev_g) if rev_g is not None else None
        mom = mom_rank_map.get(key, {})
        r_m6 = mom.get("r_m6")
        r_m12 = mom.get("r_m12")
        pre.append({"ticker":d["ticker"],"exchange":d["exchange"],
            "r_eyt":r_eyt,"r_eyf":r_eyf,"r_pb":r_pb,
            "r_epsg":r_epsg,"r_revg":r_revg,"r_m6":r_m6,"r_m12":r_m12})

    val_sums = [sum(x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None)
                for p in pre if len([x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None])>=2]
    gr_sums = [sum(x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None)
                for p in pre if len([x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None])>=3]

    results = []
    for p in pre:
        val_inputs = [x for x in [p["r_eyt"],p["r_eyf"],p["r_pb"]] if x is not None]
        gr_inputs = [x for x in [p["r_epsg"],p["r_revg"],p["r_m6"],p["r_m12"]] if x is not None]
        value_score = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs)>=2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums, sum(gr_inputs)))) if len(gr_inputs)>=3 and gr_sums else None
        results.append({
            "ticker":p["ticker"],"exchange":p["exchange"],
            "value_score":value_score,"growth_score":growth_score,
            "rank_pe_ltm":p["r_eyt"],"rank_pe_ntm":p["r_eyf"],
            "rank_pb":p["r_pb"],"rank_eps_gr":p["r_epsg"],"rank_rev_gr":p["r_revg"],
        })
    return results

rank_updates = []
for country, exchanges in RANK_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if group: rank_updates.extend(calc_ranks(group))

ranked_exchanges = set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked = [d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked: rank_updates.extend(calc_ranks(unranked))

ok = 0
for i in range(0, len(rank_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=rank_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(rank_updates[i:i+100])
print(f" Rank aggiornati: {ok}/{len(rank_updates)}")

# ── COMBINED RANK ────────────────────────────────────────────
print("\n Calcola combined rank...")
requests.patch(SUPABASE_URL+"/rest/v1/fundamentals",
    headers={**headers_up,"Prefer":"return=minimal"},
    params={"exchange":"not.eq.US"},
    json={"combined_rank": None})

all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr = [d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates = [{"ticker":d["ticker"],"exchange":d["exchange"],
    "combined_rank":min(99,pct_rank(sum_arr,d["value_score"]+d["growth_score"]))}
    for d in all_scores]

ok = 0
for i in range(0, len(combined_updates), 100):
    res = requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=combined_updates[i:i+100])
    if res.status_code in (200,201,204): ok += len(combined_updates[i:i+100])
print(f" Combined rank aggiornati: {ok}/{len(combined_updates)}")

end_time = time_module.time()
print(f"\nWeekly EU completato in {int(end_time-start_time)}s")
print("=" * 60)
