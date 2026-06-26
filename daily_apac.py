# ============================================================
# FORWARDALPHA — DAILY APAC LOAD
# Da eseguire ogni giorno alle 09:00 CET (dopo chiusura Asia)
# Copre: TSE (Giappone), SEHK (Hong Kong), ASX (Australia)
# REGOLE: vedere FORWARDALPHA_CONTEXT.md
# - prezzi scaricati da Leeway → scritti in prices_eod
# - lettura prezzi da prices_eod in chunk da 20 ticker
# - book_yield = 1/pb, PE negativi inclusi
# - combined AP = TSE+SEHK+ASX
# ============================================================

import os, math, time, requests
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
        negative = True
        s = s[1:-1]
    s = s.replace('$','').replace(',','').replace('x','').replace('%','').strip()
    if s in ['-','','N/A','nm',chr(8212)]: return None
    try:
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None

def pct_rank(vals, v):
    if v is None or not vals: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    below = sum(1 for x in vals if x < v)
    return round(below / len(vals) * 100)

def ey(pe):
    if pe is None or pe == 0: return None
    return 1.0 / pe  # PE negativi inclusi sempre

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb  # PB negativo → rank bassissimo

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
TODAY        = datetime.now().strftime("%Y-%m-%d")
TODAY_DT     = datetime.now()

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# Suffissi Leeway per exchange APAC
LEEWAY_SUFFIX = {
    "TSE":  ".T",
    "SEHK": ".HK",
    "ASX":  ".AX",
}

start_time = time.time()
print("=" * 60)
print(f"FORWARDALPHA DAILY APAC LOAD — {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO APAC DA stocks ───────────────────────
print("\n[1/5] Caricamento universo APAC...")
all_stocks = []
for exchange in ['TSE', 'SEHK', 'ASX']:
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "exchange": f"eq.{exchange}",
                    "in_universe": "eq.true", "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

print(f"  Universo APAC: {len(all_stocks)} titoli")
by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s['exchange']].append(s['ticker'])

# ── 2. SCARICA PREZZI EOD DA LEEWAY → prices_eod ────────────
print("\n[2/5] Download prezzi EOD da Leeway...")
ok_leeway = fail_leeway = 0
price_buf = []

# Prima trova la data dell'ultimo prezzo per ogni titolo
print("  Lettura ultima data prezzi...")
last_date_map = {}
for exchange, tickers in by_exchange.items():
    CHUNK = 20
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        ticker_filter = ','.join(chunk)
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "ticker,exchange,date",
                    "exchange": f"eq.{exchange}",
                    "ticker": f"in.({ticker_filter})",
                    "order": "ticker,date.desc",
                    "limit": str(len(chunk) * 2)})  # 2 righe per ticker max
        batch = r.json()
        if isinstance(batch, list):
            seen = set()
            for d in batch:
                key = (d['ticker'], d['exchange'])
                if key not in seen:
                    last_date_map[key] = d['date']
                    seen.add(key)
        time.sleep(0.01)

# Scarica prezzi da Leeway per ogni titolo
for exchange, tickers in by_exchange.items():
    suffix = LEEWAY_SUFFIX.get(exchange, '')
    print(f"  {exchange}: downloading {len(tickers)} ticker...")
    for ticker in tickers:
        key = (ticker, exchange)
        last = last_date_map.get(key, "2021-01-01")
        if last >= TODAY:
            ok_leeway += 1
            continue
        start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        leeway_ticker = ticker + suffix
        url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={start_dt}&to={TODAY}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                fail_leeway += 1
                continue
            data = r.json()
            if not isinstance(data, list) or not data:
                fail_leeway += 1
                continue
            for row in data:
                adj = row.get('adjusted_close') or row.get('close')
                if adj is None: continue
                price_buf.append({
                    "ticker": ticker,
                    "exchange": exchange,
                    "date": row['date'],
                    "adj_close": float(adj),
                })
            ok_leeway += 1
        except Exception as e:
            fail_leeway += 1

        if len(price_buf) >= 500:
            requests.post(SUPABASE_URL + "/rest/v1/prices_eod",
                          headers=headers_up, json=price_buf)
            price_buf = []
        time.sleep(0.05)

    if (ok_leeway + fail_leeway) % 200 == 0:
        print(f"    ok={ok_leeway} fail={fail_leeway}")

if price_buf:
    requests.post(SUPABASE_URL + "/rest/v1/prices_eod",
                  headers=headers_up, json=price_buf)

print(f"  Prezzi Leeway: ok={ok_leeway} fail={fail_leeway}")

# ── 3. LEGGI PREZZI DA prices_eod IN CHUNK DA 20 ────────────
print("\n[3/5] Lettura prezzi aggiornati da prices_eod...")
CHUNK = 20
all_ph = defaultdict(list)

for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        ticker_filter = ','.join(chunk)
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "ticker,date,adj_close",
                        "exchange": f"eq.{exchange}",
                        "ticker": f"in.({ticker_filter})",
                        "order": "ticker,date.desc",
                        "limit": "1000", "offset": str(offset)})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            for d in batch:
                if d['adj_close'] is not None:
                    all_ph[(d['ticker'], exchange)].append(
                        {'date': d['date'], 'close': d['adj_close']})
            offset += 1000
            if len(batch) < 1000: break
        time.sleep(0.02)

print(f"  Prezzi caricati per {len(all_ph)} titoli")

# ── 4. MOMENTUM ─────────────────────────────────────────────
print("\n[4/5] Calcolo momentum...")
ok = fail = 0
mom_updates = []

for stock in all_stocks:
    ticker   = stock['ticker']
    exchange = stock['exchange']
    data     = all_ph.get((ticker, exchange), [])

    if len(data) < 2: fail += 1; continue

    last_px   = data[0]['close']
    last_date = datetime.strptime(data[0]['date'], "%Y-%m-%d")
    chg1d     = round((data[0]['close'] / data[1]['close'] - 1) * 100, 4)

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
        "change1d": chg1d,
        "price": last_px,
    })
    ok += 1

for i in range(0, len(mom_updates), 100):
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals",
                  headers=headers_up, json=mom_updates[i:i+100])
print(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

# ── 5. RANK APAC ─────────────────────────────────────────────
print("\n[5/5] Ricalcolo rank APAC...")

all_data = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange": "in.(TSE,SEHK,ASX)", "in_universe": "eq.true",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not isinstance(data, list) or not data: break
    all_data.extend(data)
    offset += 1000
    if len(data) < 1000: break

print(f"  Fundamentals: {len(all_data)}")

mom1w_map = {(d['ticker'], d['exchange']): d.get('mom1w') for d in all_data}
mom1m_map = {(d['ticker'], d['exchange']): d.get('mom1m') for d in all_data}

def calc_ranks(group):
    ey_trail_g = [ey(d['pe_trailing']) for d in group if ey(d['pe_trailing']) is not None]
    ey_fwd_g   = [ey(d['pe_forward'])  for d in group if ey(d['pe_forward'])  is not None]
    by_g       = [book_yield(d['pb'])   for d in group if book_yield(d['pb'])  is not None]
    eps_g_vals = [d['eps_growth']       for d in group if d['eps_growth']      is not None]
    rev_g_vals = [d['rev_growth']       for d in group if d['rev_growth']      is not None]
    mom6_adj_g  = []
    mom12_adj_g = []
    for d in group:
        key = (d['ticker'], d['exchange'])
        m6  = d.get('mom6m');  m12 = d.get('mom12m')
        m1w = mom1w_map.get(key); m1m = mom1m_map.get(key)
        if m6  is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)

    pre = []
    for d in group:
        key  = (d['ticker'], d['exchange'])
        m6   = d.get('mom6m');  m12 = d.get('mom12m')
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
                    "r_epsg": r_epsg, "r_revg": r_revg,
                    "r_m6": r_m6, "r_m12": r_m12})

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
        results.append({
            "ticker": p['ticker'], "exchange": p['exchange'],
            "value_score": value_score, "growth_score": growth_score,
            "rank_pe_ltm": p['r_eyt'], "rank_pe_ntm": p['r_eyf'], "rank_pb": p['r_pb'],
            "rank_eps_gr": p['r_epsg'], "rank_rev_gr": p['r_revg'],
            "rank_mom6_adj": p['r_m6'], "rank_mom12_adj": p['r_m12'],
        })
    return results

# Rank per paese separati
APAC_GROUPS = {"JPN": ["TSE"], "HKG": ["SEHK"], "AUS": ["ASX"]}
rank_updates = []
for country, exchanges in APAC_GROUPS.items():
    group = [d for d in all_data if d['exchange'] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f"  {country}: {len(res)} titoli rankati")

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals",
                      headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print(f"  Rank paese: {ok}/{len(rank_updates)}")

# Combined rank — aggiorna direttamente senza azzerare prima

all_scores = [d for d in rank_updates
              if d.get('value_score') is not None and d.get('growth_score') is not None]
comb_arr   = [d['value_score'] + d['growth_score'] for d in all_scores]
combined_updates = [{
    "ticker": d['ticker'], "exchange": d['exchange'],
    "combined_rank": min(99, int(round(pct_rank(comb_arr, d['value_score'] + d['growth_score']))))
} for d in all_scores]

ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals",
                      headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print(f"  Combined rank APAC (TSE+SEHK+ASX): {ok}/{len(combined_updates)}")
ok_rank = ok

# ── LOG ──────────────────────────────────────────────────────
end_time = time.time()
log_entry = {
    "run_date": TODAY, "market": "APAC",
    "prices_updated": ok_leeway, "prices_failed": fail_leeway,
    "last_price_date": TODAY,
    "momentum_updated": ok_momentum, "rank_updated": ok_rank,
    "duration_seconds": int(end_time - start_time),
}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
print(f"\nLog: leeway={ok_leeway} fail={fail_leeway} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n" + "=" * 60)
print("DAILY APAC LOAD COMPLETATO")
print("=" * 60)
