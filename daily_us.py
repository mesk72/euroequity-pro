# ============================================================
# FORWARDALPHA — DAILY US+CA LOAD
# Da eseguire ogni giorno alle 23:00 CET (dopo chiusura US)
# REGOLE: FORWARDALPHA_CONTEXT.md
# - universo: US + TSX (Canada) = ~2400 titoli
# - prezzi da Leeway → prices_eod (chunk 20)
# - book_yield = 1/pb (PB negativi inclusi)
# - PE negativi inclusi sempre
# - combined NA = US+TSX insieme
# ============================================================

import os, math, time, time as time_module, requests
from datetime import datetime, timedelta
from collections import defaultdict

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
    return int(round(below / len(valid) * 100))

def ey(pe):
    if pe is None or pe == 0: return None
    return 1.0 / pe  # PE negativi inclusi sempre

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb  # PB negativi inclusi

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
TODAY        = datetime.now().strftime("%Y-%m-%d")

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# Suffissi Leeway per US e TSX
LEEWAY_SUFFIX = {"US": ".US", "TSX": ".TO"}

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA DAILY US+CA LOAD — {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO US + TSX ──────────────────────────────
print("\n[1/5] Caricamento universo US+CA...")
all_stocks = []
for exchange in ['US', 'TSX']:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": f"eq.{exchange}", "offset": str(offset), "limit": "1000"})
        if not r.text or r.text == "[]": break
        try: data = r.json()
        except: break
        if not data: break
        all_stocks.extend(data)
        offset += 1000
        if len(data) < 1000: break

print(f"  Universo US+CA: {len(all_stocks)} titoli")
by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s['exchange']].append(s['ticker'])
for ex, tks in by_exchange.items():
    print(f"    {ex}: {len(tks)}")

# ── 2. SCARICA PREZZI EOD DA LEEWAY → prices_eod ────────────
print("\n[2/5] Download prezzi EOD da Leeway...")
CHUNK = 20

# Leggi ultima data prezzi
ok_leeway = fail_leeway = 0
price_buf = []
for stock in all_stocks:
    ticker   = stock['ticker']
    exchange = stock['exchange']
    # Stessa logica Yahoo: 1 query per ticker per trovare ultima data
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date,adj_close", "ticker": f"eq.{ticker}",
                "exchange": f"eq.{exchange}", "order": "date.desc", "limit": "1"})
    row = r.json()
    last          = row[0]["date"]      if isinstance(row, list) and row else "2021-01-01"
    last_close_db = row[0]["adj_close"] if isinstance(row, list) and row else None
    if last >= TODAY:
        ok_leeway += 1
        continue
    start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    lt = ticker + LEEWAY_SUFFIX.get(exchange, "")
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={start_dt}&to={TODAY}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            fail_leeway += 1
            continue
        data_l = resp.json()
        if not isinstance(data_l, list) or not data_l:
            fail_leeway += 1
            continue
        for row2 in data_l:
            adj = row2.get('adjusted_close') or row2.get('close')
            if adj is None: continue
            price_buf.append({
                "ticker": ticker, "exchange": exchange,
                "date": row2['date'], "adj_close": float(adj),
            })
        ok_leeway += 1
    except:
        fail_leeway += 1

    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        price_buf = []
    time.sleep(0.05)
print(f"  Prezzi Leeway: ok={ok_leeway} fail={fail_leeway}")
ok_prices = ok_leeway; fail_prices = fail_leeway

# ── 3. LEGGI PREZZI DA prices_eod (chunk 20) ────────────────
print("\n[3/5] Lettura prezzi da prices_eod...")
all_ph = defaultdict(list)
for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        offset_p = 0
        while True:
            rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "ticker,date,adj_close",
                        "exchange": f"eq.{exchange}",
                        "ticker": f"in.({','.join(chunk)})",
                        "order": "ticker,date.desc",
                        "limit": "1000", "offset": str(offset_p)})
            batch = rp.json()
            if not isinstance(batch, list) or not batch: break
            for d in batch:
                if d['adj_close'] is not None:
                    all_ph[(d['ticker'], exchange)].append(
                        {'date': d['date'], 'close': d['adj_close']})
            offset_p += 1000
            if len(batch) < 1000: break
        time.sleep(0.02)
print(f"  Prezzi caricati: {len(all_ph)} titoli")

# ── 4. MOMENTUM ──────────────────────────────────────────────
print("\n[4/5] Calcolo momentum...")
ok = fail = 0
mom_updates = []
for stock in all_stocks:
    ticker = stock['ticker']; exchange = stock['exchange']
    data = all_ph.get((ticker, exchange), [])
    if len(data) < 2: fail += 1; continue
    last_px   = data[0]['close']
    last_date = datetime.strptime(data[0]['date'], "%Y-%m-%d")
    chg1d = round((data[0]['close'] / data[1]['close'] - 1) * 100, 4)

    def mom_cal(days):
        target  = last_date - timedelta(days=days)
        closest = min(data, key=lambda x: abs((datetime.strptime(x['date'], "%Y-%m-%d") - target).days))
        if closest['close'] and closest['close'] != 0:
            return round(last_px / closest['close'] - 1, 6)
        return None

    mom_updates.append({
        "ticker": ticker, "exchange": exchange,
        "mom1w": mom_cal(7), "mom1m": mom_cal(31),
        "mom6m": mom_cal(182), "mom12m": mom_cal(365),
        "change1d": chg1d, "price": last_px,
    })
    ok += 1

for i in range(0, len(mom_updates), 100):
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=mom_updates[i:i+100])
print(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

# ── 5. RANK US+CA ────────────────────────────────────────────
print("\n[5/5] Ricalcolo rank US+CA...")
all_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange": "in.(US,TSX)", "in_universe": "eq.true",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not isinstance(data, list) or not data: break
    all_data.extend(data); offset += 1000
    if len(data) < 1000: break
print(f"  Fundamentals: {len(all_data)}")

mom1w_map = {(d['ticker'], d['exchange']): d.get('mom1w') for d in all_data}
mom1m_map = {(d['ticker'], d['exchange']): d.get('mom1m') for d in all_data}

# Rank US e CA separati per value/growth
RANK_GROUPS = {"USA": ["US"], "CAN": ["TSX"]}

def calc_ranks(group):
    ey_trail_g = [ey(d['pe_trailing']) for d in group if ey(d['pe_trailing']) is not None]
    ey_fwd_g   = [ey(d['pe_forward'])  for d in group if ey(d['pe_forward'])  is not None]
    by_g       = [book_yield(d['pb'])   for d in group if book_yield(d['pb'])  is not None]
    eps_g_vals = [d['eps_growth']       for d in group if d['eps_growth']      is not None]
    rev_g_vals = [d['rev_growth']       for d in group if d['rev_growth']      is not None]
    mom6_adj_g = []; mom12_adj_g = []
    for d in group:
        key = (d['ticker'], d['exchange'])  # CORRETTO: usa d['exchange']
        m6  = d.get('mom6m'); m12 = d.get('mom12m')
        m1w = mom1w_map.get(key); m1m = mom1m_map.get(key)
        if m6  is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    pre = []
    for d in group:
        key  = (d['ticker'], d['exchange'])
        m6   = d.get('mom6m'); m12 = d.get('mom12m')
        m1w  = mom1w_map.get(key); m1m = mom1m_map.get(key)
        ey_t = ey(d.get('pe_trailing')); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        ey_f = ey(d.get('pe_forward'));  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
        by_v = book_yield(d.get('pb'));  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
        r_epsg = pct_rank(eps_g_vals, d.get('eps_growth')) if d.get('eps_growth') is not None else None
        r_revg = pct_rank(rev_g_vals, d.get('rev_growth')) if d.get('rev_growth') is not None else None
        mom6_adj  = (m6  - m1w) if m6  is not None and m1w is not None else None
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
                        "rank_pe_ltm": p['r_eyt'], "rank_pe_ntm": p['r_eyf'], "rank_pb": p['r_pb'],
                        "rank_eps_gr": p['r_epsg'], "rank_rev_gr": p['r_revg'],
                        "rank_mom6_adj": p['r_m6'], "rank_mom12_adj": p['r_m12']})
    return results

rank_updates = []
for country, exchanges in RANK_GROUPS.items():
    group = [d for d in all_data if d['exchange'] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f"  {country}: {len(res)} rankati")

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print(f"  Rank US+CA: {ok}/{len(rank_updates)}")

# Combined rank NA = US+TSX insieme
requests.patch(SUPABASE_URL + "/rest/v1/fundamentals",
    headers={**headers_up, "Prefer": "return=minimal"},
    params={"exchange": "in.(US,TSX)"},
    json={"combined_rank": None})
all_scores = [d for d in rank_updates if d.get('value_score') is not None and d.get('growth_score') is not None]
comb_arr   = [d['value_score'] + d['growth_score'] for d in all_scores]
combined_updates = [{"ticker": d['ticker'], "exchange": d['exchange'],
                     "combined_rank": min(99, int(round(pct_rank(comb_arr, d['value_score'] + d['growth_score']))))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print(f"  Combined rank NA (US+TSX): {ok}/{len(combined_updates)}")
ok_rank = ok

# ── INDICI NORD AMERICA ──────────────────────────────────────
print("\n  Aggiornamento indici Nord America...")
NA_INDICES = [
    ("^DJI","US","DJI","Dow Jones"), ("^GSPC","US","GSPC","S&P 500"),
    ("^IXIC","US","IXIC","Nasdaq"), ("^GSPTSE","TSX","GSPTSE.INDX","TSX"),
]
ok_idx = 0
for db_ticker, exchange, lt, name in NA_INDICES:
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={TODAY}&to={TODAY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
        if not data:
            ieri = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            r2 = requests.get(f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={ieri}&to={TODAY}", timeout=10)
            data = r2.json() if r2.status_code == 200 and isinstance(r2.json(), list) else []
        if not data: continue
        # Ordina per data ASC per avere last e prev corretti
        data_sorted = sorted(data, key=lambda x: x["date"])
        rows = [{"ticker": db_ticker, "exchange": exchange, "date": d["date"], "close": d["adjusted_close"]}
                for d in data_sorted if d.get("adjusted_close")]
        if rows:
            requests.post(SUPABASE_URL + "/rest/v1/price_history", headers=headers_up, json=rows)
        price = float(data_sorted[-1]["adjusted_close"])
        prev  = float(data_sorted[-2]["adjusted_close"]) if len(data_sorted) >= 2 else None
        change1d = round((price / prev - 1) * 100, 2) if prev and prev != 0 else None
        requests.patch(SUPABASE_URL + "/rest/v1/indices", headers=headers_up,
            params={"ticker": f"eq.{db_ticker}"},
            json={"price": price, "change1d": change1d, "date": data[-1]["date"]})
        print(f"  {name}: {price} ({change1d}%)")
        ok_idx += 1
    except Exception as e: print(f"  ERR {name}: {e}")
    time.sleep(0.2)
print(f"  Indici NA: {ok_idx}/{len(NA_INDICES)}")

end_time = time_module.time()
log_entry = {"run_date": TODAY, "market": "US+CA", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
print(f"\nLog: leeway={ok_prices} fail={fail_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n" + "=" * 60)
print("DAILY US+CA LOAD COMPLETATO")
print("=" * 60)
