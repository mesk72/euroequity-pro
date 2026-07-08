# ============================================================
# FORWARDALPHA — WEEKLY APAC LOAD
# Da eseguire ogni domenica alle 10:00 CET
# Copre: TSE (Giappone), SEHK (Hong Kong), ASX (Australia), KRX (Corea), SGX (Singapore)
# REGOLE: FORWARDALPHA_CONTEXT.md
# - CSV TIKR: tikr_apac_latest.csv in Supabase storage
# - SEHK ticker: lstrip('0') prima del match
# - calendarizzazione dinamica
# - book_yield = 1/pb
# - combined AP = TSE+SEHK+ASX+KRX+SGX
# - TSX (Canada) = combined con US nel weekly_us
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

# Mapping exchange TIKR → DB
EX_MAP_APAC = {
    "TSE": "TSE", "TYO": "TSE", "XTKS": "TSE",
    "SEHK": "SEHK", "HKG": "SEHK", "XHKG": "SEHK",
    "ASX": "ASX", "XASX": "ASX",
    "KOSE": "KRX", "KOSDAQ": "KRX",
    "SGX": "SGX", "Catalist": "SGX", "NSE": "SGX", "SPSE": "SGX", "NSX": "SGX", "XKON": "SGX",
    # TSX/Canada escluso — Canada va nel weekly_us con tikr_us_latest.csv
}

TARGETS = {"TSE": 1000, "SEHK": 500, "ASX": 350, "KRX": 400, "SGX": 100}
# TSX non incluso — Canada rankato con US nel weekly_us

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
    return 1.0 / pe  # PE negativi inclusi sempre

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb  # PB negativi inclusi

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA WEEKLY APAC LOAD — {TODAY}")
print("=" * 60)

# ── FISCAL YEAR END ──────────────────────────────────────────
print("\n Legge fiscal year end...")
TIKR_FY_EXCHANGE_MAP = {
    "NasdaqGS": "US", "NasdaqGM": "US", "NasdaqCM": "US",
    "NYSE": "US", "NYSEAM": "US", "ARCA": "US", "BATS": "US",
    "OTCPK": "US", "CNSX": "US",
    "JPX": "TSE", "HKEX": "SEHK", "KOSDAQ": "KRX",
    "TSXV": "TSX",
    "Catalist": "SGX",
}
def _norm_fy_exchange(raw):
    return TIKR_FY_EXCHANGE_MAP.get(raw, raw)

fy_map = {}
try:
    r_fy = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_fy.text))
    for row in reader:
        ticker   = row["ticker"].strip()
        exchange = _norm_fy_exchange(row["exchange"].strip())
        month    = parse_num(row.get("fiscal_month","12"))
        fy_map[(ticker, exchange)] = int(month) if month else 12
    print(f" FY end: {len(fy_map)}")
except Exception as e:
    print(f" FY end non trovato: {e}")

def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)

def calendarize(ticker, exchange, fy2025, fy2026, fy2027, fy2028, today_dt):
    """Calendarizzazione DINAMICA.
    Se il pub_date del ciclo piu' recente non e' ancora arrivato, resta
    sul ciclo precedente invece di saltare in avanti — elimina il salto not_yet."""
    if fy2025 is None and fy2026 is None: return None, None, True
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm==2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year-1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        fy_end = datetime(fy_end.year-1, fm, last_day)
        pub_date = fy_end + timedelta(days=60)
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

# ── LEGGE STOCKS DAL DB (per match ticker) ───────────────────
print("\n Legge stocks APAC dal DB...")
stocks_tickers = {"TSE": set(), "SEHK": set(), "ASX": set(), "KRX": set(), "SGX": set()}
for exchange in ["TSE", "SEHK", "ASX", "KRX", "SGX"]:
    offset = 0
    while True:
        try:
            r = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
                params={"select":"ticker","exchange":f"eq.{exchange}","in_universe":"eq.true",
                        "limit":"1000","offset":str(offset)}, timeout=20)
            batch = r.json()
        except Exception as e:
            print(f" WARN lettura stocks {exchange}: {e}"); break
        if not isinstance(batch,list) or not batch: break
        for d in batch: stocks_tickers[exchange].add(d["ticker"])
        offset += 1000
        if len(batch) < 1000: break
    print(f" {exchange}: {len(stocks_tickers[exchange])} in_universe=true nel DB")

# ── TIKR APAC ────────────────────────────────────────────────
print("\n Legge file TIKR APAC...")
tikr_rows = []
try:
    r_tikr = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv",
        headers=headers_r)
    reader = csv.DictReader(io.StringIO(r_tikr.text))
    raw_rows = []
    for row in reader:
        ex_tikr  = row.get("Primary Exchange","").strip()
        exchange = EX_MAP_APAC.get(ex_tikr, "")
        if not exchange: continue
        # SEHK: lstrip zeros
        if exchange == "SEHK":
            ticker = str(row["Ticker"]).strip().lstrip("0")
        else:
            ticker = str(row["Ticker"]).strip()
        if not ticker: continue
        mktcap = parse_num(row.get("Last Mkt Cap",""))
        raw_rows.append({
            "ticker": ticker, "exchange": exchange,
            "mktcap": mktcap or 0,
            "pe_trailing": parse_num(row.get("LTM P/E LTM","")),
            "pe_forward":  parse_num(row.get("Mean Fwd P/E NTM","")),
            "pb":          parse_num(row.get("LTM P/BVPS LTM","")),
            "eps_fy0": parse_num(row.get("EPS Normalized (FY 2025)","")),
            "eps_fy1": parse_num(row.get("Mean EPS Normalized (FY 2026)","")),
            "eps_fy2": parse_num(row.get("Mean EPS Normalized (FY 2027)","")),
            "eps_fy3": parse_num(row.get("Mean EPS Normalized (FY 2028)","")),
            "rev_fy0": parse_num(row.get("Rev (FY 2025)","")),
            "rev_fy1": parse_num(row.get("Mean Rev (FY 2026)","")),
            "rev_fy2": parse_num(row.get("Mean Rev (FY 2027)","")),
            "rev_fy3": parse_num(row.get("Mean Rev (FY 2028)","")),
        })

    # Per ogni exchange: filtra solo titoli presenti nel DB, top N per mktcap
    from collections import defaultdict

    def _norm_krx(t):
        return t.lstrip("A") if t else t

    # Mappa ticker-normalizzato -> ticker-vero-in-stocks (per KRX, dove i
    # due file possono differire sul prefisso "A"). Il ticker scritto in
    # fundamentals deve SEMPRE combaciare esattamente con stocks.ticker.
    krx_norm_to_real = {_norm_krx(t): t for t in stocks_tickers["KRX"]}
    stocks_tickers["KRX"] = set(krx_norm_to_real.keys())  # per il check di appartenenza sotto

    by_ex = defaultdict(list)
    for r in raw_rows:
        if r["exchange"] == "KRX":
            ticker_norm = _norm_krx(r["ticker"])
            if ticker_norm in stocks_tickers["KRX"]:
                r["ticker"] = krx_norm_to_real[ticker_norm]  # usa il ticker vero di stocks
                by_ex[r["exchange"]].append(r)
        else:
            if r["ticker"] in stocks_tickers.get(r["exchange"], set()):
                by_ex[r["exchange"]].append(r)

    print(f" DEBUG: candidati SGX nel file TIKR (raw_rows): {len([r for r in raw_rows if r['exchange']=='SGX'])}")
    print(f" DEBUG: ticker SGX in stocks_tickers: {len(stocks_tickers['SGX'])}")
    print(f" DEBUG: primi 5 ticker SGX dal TIKR: {[r['ticker'] for r in raw_rows if r['exchange']=='SGX'][:5]}")
    print(f" DEBUG: primi 5 ticker SGX in stocks: {list(stocks_tickers['SGX'])[:5]}")

    for exchange, target in TARGETS.items():
        # stocks_tickers ora contiene SOLO in_universe=true (la selezione
        # ufficiale di universe_apac_unified.py) — non si ricalcola piu'
        # una top-N indipendente qui, si usano esattamente quei titoli.
        rows = sorted(by_ex[exchange], key=lambda x: x["mktcap"], reverse=True)
        tikr_rows.extend(rows)
        print(f" TIKR {exchange}: {len(rows)} (in_universe ufficiale, target di riferimento={target})")
    # Log Canada se presente nel CSV (viene ignorato)
    if by_ex.get("TSX"):
        print(f" TIKR TSX: ignorato ({len(by_ex['TSX'])} righe) — Canada va in tikr_us_latest.csv")

    print(f" TIKR APAC totale: {len(tikr_rows)}")
except Exception as e:
    print(f" Errore TIKR APAC: {e}"); exit()

# Set delle coppie (ticker, exchange) effettivamente in universo per questo run
universe_keys = {(r["ticker"], r["exchange"]) for r in tikr_rows}

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
        "mkt_cap": round(r["mktcap"], 2) if r["mktcap"] else None,
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
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=fund_updates[i:i+100], timeout=30)
        if r.status_code in (200, 201, 204): ok += len(fund_updates[i:i+100])
    except Exception as e:
        print(f" WARN salvataggio fondamentali batch {i}: {e}")
print(f" Fondamentali: {ok}/{len(fund_updates)}")

# ── MOMENTUM DAL DB ──────────────────────────────────────────
mom_rank_map = {}
offset = 0
while True:
    try:
        res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,rank_mom6_adj,rank_mom12_adj",
                    "exchange":"in.(TSE,SEHK,ASX,KRX,SGX)",
                    "offset":str(offset),"limit":"1000"}, timeout=20)
        data = res.json()
    except Exception as e:
        print(f" WARN lettura momentum: {e}"); break
    if not isinstance(data, list) or not data: break
    for d in data:
        if (d["ticker"],d["exchange"]) not in universe_keys: continue
        mom_rank_map[(d["ticker"],d["exchange"])] = {
            "r_m6": d.get("rank_mom6_adj"), "r_m12": d.get("rank_mom12_adj")}
    offset += 1000
    if len(data) < 1000: break
print(f" Momentum: {len(mom_rank_map)}")

# ── FONDAMENTALI DB ──────────────────────────────────────────
all_data = []
offset = 0
while True:
    try:
        res = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth",
                    "exchange":"in.(TSE,SEHK,ASX,KRX,SGX)",
                    "offset":str(offset),"limit":"1000"}, timeout=20)
        data = res.json()
    except Exception as e:
        print(f" WARN lettura fondamentali: {e}"); break
    if not isinstance(data, list) or not data: break
    all_data.extend([d for d in data if (d["ticker"],d["exchange"]) in universe_keys])
    offset += 1000
    if len(data) < 1000: break
print(f" Fondamentali DB: {len(all_data)}")

# ── RANK PER PAESE ───────────────────────────────────────────
APAC_GROUPS = {"JPN": ["TSE"], "HKG": ["SEHK"], "AUS": ["ASX"], "KOR": ["KRX"], "SGP": ["SGX"]}

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
for country, exchanges in APAC_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f" {country}: {len(res)}")

ok = 0
for i in range(0, len(rank_updates), 100):
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100], timeout=30)
        if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
    except Exception as e:
        print(f" WARN salvataggio rank batch {i}: {e}")
print(f" Rank APAC paese: {ok}/{len(rank_updates)}")

# ── COMBINED APAC = TSE+SEHK+ASX+KRX+SGX ────────────────────
# combined_rank NON azzerato — aggiorna direttamente con merge-duplicates
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
comb_arr   = [d["value_score"]+d["growth_score"] for d in all_scores]
combined_updates = [{"ticker":d["ticker"],"exchange":d["exchange"],
                     "combined_rank":min(99,pct_rank(comb_arr,d["value_score"]+d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100], timeout=30)
        if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
    except Exception as e:
        print(f" WARN salvataggio combined batch {i}: {e}")
print(f" Combined APAC (TSE+SEHK+ASX+KRX+SGX): {ok}/{len(combined_updates)}")

end_time = time_module.time()
print(f"\nWeekly APAC completato in {int(end_time-start_time)}s")
print("=" * 60)
