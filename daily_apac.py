# ============================================================
# FORWARDALPHA — DAILY APAC LOAD
# Da eseguire ogni giorno alle 09:00 CET (dopo chiusura Asia)
# Copre: TSE (Giappone), SEHK (Hong Kong), ASX (Australia), KRX (Corea), SGX (Singapore)
# ============================================================

import os, math, time, time as time_module, requests
from datetime import datetime, timedelta
from collections import defaultdict

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
    return 1.0 / pe

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
TODAY        = datetime.now().strftime("%Y-%m-%d")
TODAY_DT     = datetime.now()

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

def leeway_ticker(ticker, exchange):
    if exchange == "TSE":
        return ticker + ".TSE"         # es. 7203.TSE
    elif exchange == "SEHK":
        return ticker.zfill(4) + ".HK" # es. 0700.HK
    elif exchange == "ASX":
        return ticker + ".AU"          # es. BHP.AU
    elif exchange == "KRX":
        return ticker.lstrip("A").zfill(6) + ".KO"  # es. 005930.KO (Samsung)
    elif exchange == "SGX":
        return ticker + ".SG"          # es. D05.SG
    return ticker

start_time = time_module.time()
print("=" * 60)
print(f"FORWARDALPHA DAILY APAC LOAD — {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO APAC ──────────────────────────────────
print("\n[1/5] Caricamento universo APAC...")
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker", "in_universe": "eq.true",
                "exchange": "in.(TSE,SEHK,ASX,KRX,SGX)",
                "offset": str(offset), "limit": "1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"  Universo APAC: {len(all_stocks)} titoli")

by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s["exchange"]].append(s["ticker"])

# ── 2. SCARICA PREZZI EOD DA LEEWAY ──────────────────────────
print("\n[2/5] Download prezzi EOD da Leeway...")
ok_leeway = fail_leeway = 0
price_buf = []
for stock in all_stocks:
    ticker   = stock["ticker"]
    exchange = stock["exchange"]
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date", "ticker": "eq." + ticker,
                    "exchange": "eq." + exchange, "order": "date.desc", "limit": "1"},
            timeout=15)
        row = r.json()
        last = row[0]["date"] if isinstance(row, list) and row else "2021-01-01"
    except Exception as e:
        print(f"  WARN lettura ultima data {ticker}.{exchange}: {e}")
        fail_leeway += 1
        continue
    if last >= TODAY:
        ok_leeway += 1
        continue
    start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    lt  = leeway_ticker(ticker, exchange)
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + start_dt + "&to=" + TODAY
    try:
        resp = requests.get(url, timeout=15)
        data_l = resp.json() if resp.status_code == 200 else []
        # Fallback: usa yahoo_ticker se il ticker principale fallisce
        if not isinstance(data_l, list) or not data_l:
            yt = stock.get("yahoo_ticker", "")
            if yt:
                # Costruisci ticker Leeway dal yahoo_ticker rimuovendo suffisso Yahoo
                yt_base = yt.split(".")[0] if "." in yt else yt
                lt2 = leeway_ticker(yt_base, exchange)
                if lt2 != lt:
                    resp2 = requests.get(LEEWAY_BASE + "/historicalquotes/" + lt2 + "?apitoken=" + LEEWAY_KEY + "&from=" + start_dt + "&to=" + TODAY, timeout=15)
                    data_l = resp2.json() if resp2.status_code == 200 else []
        if not isinstance(data_l, list) or not data_l: fail_leeway += 1; continue
        for row2 in data_l:
            adj = row2.get("adjusted_close") or row2.get("close")
            if adj is None: continue
            price_buf.append({"ticker": ticker, "exchange": exchange,
                               "date": row2["date"], "adj_close": float(adj)})
        ok_leeway += 1
    except: fail_leeway += 1
    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        price_buf = []
    time.sleep(0.5)
if price_buf:
    requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
print(f"  Prezzi Leeway: ok={ok_leeway} fail={fail_leeway}")
ok_prices = ok_leeway; fail_prices = fail_leeway

# ── 3. LEGGI PREZZI DA prices_eod ────────────────────────────
print("\n[3/5] Lettura prezzi da prices_eod...")
CHUNK = 20
all_ph = defaultdict(list)
for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        offset_p = 0
        # Limita a ultimi 400 giorni — sufficiente per momentum 12 mesi
        from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        while True:
            rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "ticker,date,adj_close",
                        "exchange": "eq." + exchange,
                        "ticker": "in.(" + ",".join(chunk) + ")",
                        "date": "gte." + from_400d,
                        "order": "ticker,date.desc",
                        "limit": "1000", "offset": str(offset_p)})
            batch = rp.json()
            if not isinstance(batch, list) or not batch: break
            for d in batch:
                if d["adj_close"] is not None:
                    all_ph[(d["ticker"], exchange)].append(
                        {"date": d["date"], "close": d["adj_close"]})
            offset_p += 1000
            if len(batch) < 1000: break
        time.sleep(0.02)
print(f"  Prezzi caricati: {len(all_ph)} titoli")

# ── 4. MOMENTUM ──────────────────────────────────────────────
print("\n[4/5] Calcolo momentum...")
ok = fail = 0
mom_updates = []
SPLIT_THRESHOLD_PCT = 20
split_suspects = []
for stock in all_stocks:
    ticker = stock["ticker"]; exchange = stock["exchange"]
    data = all_ph.get((ticker, exchange), [])
    if len(data) < 2: fail += 1; continue
    last_px   = data[0]["close"]
    last_date = datetime.strptime(data[0]["date"], "%Y-%m-%d")
    chg1d = round((data[0]["close"] / data[1]["close"] - 1) * 100, 4)
    if abs(chg1d) > SPLIT_THRESHOLD_PCT:
        split_suspects.append((ticker, exchange, chg1d))

    def mom_cal(days):
        target  = last_date - timedelta(days=days)
        closest = min(data, key=lambda x: abs((datetime.strptime(x["date"], "%Y-%m-%d") - target).days))
        if closest["close"] and closest["close"] != 0:
            return round(last_px / closest["close"] - 1, 6)
        return None

    mom_updates.append({"ticker": ticker, "exchange": exchange,
                         "mom1w": mom_cal(7), "mom1m": mom_cal(31),
                         "mom6m": mom_cal(182), "mom12m": mom_cal(365),
                         "change1d": chg1d, "price": last_px})
    ok += 1

# Se un titolo varia di oltre SPLIT_THRESHOLD_PCT in un giorno, probabile
# stock split non segnalato da Leeway: ricarica tutto lo storico a 5 anni.
if split_suspects:
    print(f"\n  Rilevati {len(split_suspects)} possibili stock split (variazione 1gg > {SPLIT_THRESHOLD_PCT}%): ricarico 5 anni di storico...")
    FROM_5Y = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
    mom_by_key = {(u["ticker"], u["exchange"]): u for u in mom_updates}
    for ticker, exchange, old_chg in split_suspects:
        lt = leeway_ticker(ticker, exchange)
        url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_5Y + "&to=" + TODAY
        try:
            resp = requests.get(url, timeout=20)
            data_l = resp.json() if resp.status_code == 200 else []
            if not isinstance(data_l, list) or not data_l:
                print(f"    {ticker}.{exchange}: nessun dato storico da Leeway (variazione era {old_chg}%), salto")
                continue
            requests.delete(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up,
                params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})
            new_rows = []
            for row2 in data_l:
                adj = row2.get("adjusted_close") or row2.get("close")
                if adj is None: continue
                new_rows.append({"ticker": ticker, "exchange": exchange,
                                  "date": row2["date"], "adj_close": float(adj)})
            for i in range(0, len(new_rows), 500):
                requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=new_rows[i:i+500])
            new_sorted = sorted(new_rows, key=lambda x: x["date"], reverse=True)
            if len(new_sorted) >= 2:
                last_px2   = new_sorted[0]["adj_close"]
                last_date2 = datetime.strptime(new_sorted[0]["date"], "%Y-%m-%d")
                new_chg1d  = round((new_sorted[0]["adj_close"] / new_sorted[1]["adj_close"] - 1) * 100, 4)

                def mom_cal2(days):
                    target  = last_date2 - timedelta(days=days)
                    closest = min(new_sorted, key=lambda x: abs((datetime.strptime(x["date"], "%Y-%m-%d") - target).days))
                    if closest["adj_close"] and closest["adj_close"] != 0:
                        return round(last_px2 / closest["adj_close"] - 1, 6)
                    return None

                key = (ticker, exchange)
                if key in mom_by_key:
                    mom_by_key[key].update({
                        "mom1w": mom_cal2(7), "mom1m": mom_cal2(31),
                        "mom6m": mom_cal2(182), "mom12m": mom_cal2(365),
                        "change1d": new_chg1d, "price": last_px2,
                    })
                print(f"    {ticker}.{exchange}: ricaricato ({len(new_rows)} righe), variazione ricalcolata {new_chg1d}%")
        except Exception as e:
            print(f"    {ticker}.{exchange}: errore ricarica — {e}")
        time.sleep(0.3)

for i in range(0, len(mom_updates), 100):
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=mom_updates[i:i+100])
print(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

# ── 5. RANK APAC ─────────────────────────────────────────────
print("\n[5/5] Ricalcolo rank APAC...")
all_data = []
offset = 0
# in_universe vive in stocks non in fundamentals — usa universe_keys
# (stesso fix già applicato in daily_eu.py e daily_us.py)
universe_keys = {(s["ticker"], s["exchange"]) for s in all_stocks}
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange": "in.(TSE,SEHK,ASX,KRX,SGX)",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not isinstance(data, list) or not data: break
    all_data.extend([d for d in data if (d["ticker"], d["exchange"]) in universe_keys])
    offset += 1000
    if len(data) < 1000: break
print(f"  Fundamentals: {len(all_data)}")

# Mom maps da mom_updates (prezzi appena scaricati) NON dal DB vecchio
mom1w_map  = {(d["ticker"], d["exchange"]): d.get("mom1w")  for d in mom_updates}
mom1m_map  = {(d["ticker"], d["exchange"]): d.get("mom1m")  for d in mom_updates}
mom6m_map  = {(d["ticker"], d["exchange"]): d.get("mom6m")  for d in mom_updates}
mom12m_map = {(d["ticker"], d["exchange"]): d.get("mom12m") for d in mom_updates}

RANK_GROUPS = {"JPN": ["TSE"], "HKG": ["SEHK"], "AUS": ["ASX"], "KOR": ["KRX"], "SGP": ["SGX"]}

def calc_ranks(group):
    ey_trail_g = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g   = [ey(d["pe_forward"])  for d in group if ey(d["pe_forward"])  is not None]
    by_g       = [book_yield(d["pb"])   for d in group if book_yield(d["pb"])  is not None]
    eps_g_vals = [d["eps_growth"]       for d in group if d["eps_growth"]      is not None]
    rev_g_vals = [d["rev_growth"]       for d in group if d["rev_growth"]      is not None]
    mom6_adj_g = []; mom12_adj_g = []
    for d in group:
        key = (d["ticker"], d["exchange"])
        m6  = mom6m_map.get(key, d.get("mom6m"))
        m12 = mom12m_map.get(key, d.get("mom12m"))
        m1w = mom1w_map.get(key, d.get("mom1w"))
        m1m = mom1m_map.get(key, d.get("mom1m"))
        if m6  is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    pre = []
    for d in group:
        key  = (d["ticker"], d["exchange"])
        m6   = mom6m_map.get(key, d.get("mom6m"))
        m12  = mom12m_map.get(key, d.get("mom12m"))
        m1w  = mom1w_map.get(key, d.get("mom1w"))
        m1m  = mom1m_map.get(key, d.get("mom1m"))
        ey_t = ey(d.get("pe_trailing")); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
        ey_f = ey(d.get("pe_forward"));  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
        by_v = book_yield(d.get("pb"));  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
        r_epsg = pct_rank(eps_g_vals, d.get("eps_growth")) if d.get("eps_growth") is not None else None
        r_revg = pct_rank(rev_g_vals, d.get("rev_growth")) if d.get("rev_growth") is not None else None
        mom6_adj  = (m6  - m1w) if m6  is not None and m1w is not None else None
        mom12_adj = (m12 - m1m) if m12 is not None and m1m is not None else None
        r_m6  = pct_rank(mom6_adj_g,  mom6_adj)  if mom6_adj  is not None else None
        r_m12 = pct_rank(mom12_adj_g, mom12_adj) if mom12_adj is not None else None
        pre.append({"ticker": d["ticker"], "exchange": d["exchange"],
                    "r_eyt": r_eyt, "r_eyf": r_eyf, "r_pb": r_pb,
                    "r_epsg": r_epsg, "r_revg": r_revg, "r_m6": r_m6, "r_m12": r_m12})
    val_sums = [sum(x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None)
                for p in pre if len([x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None]) >= 2]
    gr_sums  = [sum(x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None)
                for p in pre if len([x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None]) >= 3]
    results = []
    for p in pre:
        val_inputs = [x for x in [p["r_eyt"], p["r_eyf"], p["r_pb"]] if x is not None]
        gr_inputs  = [x for x in [p["r_epsg"], p["r_revg"], p["r_m6"], p["r_m12"]] if x is not None]
        value_score  = int(round(pct_rank(val_sums, sum(val_inputs)))) if len(val_inputs) >= 2 and val_sums else None
        growth_score = int(round(pct_rank(gr_sums,  sum(gr_inputs))))  if len(gr_inputs) >= 3 and gr_sums  else None
        results.append({"ticker": p["ticker"], "exchange": p["exchange"],
                        "value_score": value_score, "growth_score": growth_score,
                        "rank_pe_ltm": p["r_eyt"], "rank_pe_ntm": p["r_eyf"], "rank_pb": p["r_pb"],
                        "rank_eps_gr": p["r_epsg"], "rank_rev_gr": p["r_revg"],
                        "rank_mom6_adj": p["r_m6"], "rank_mom12_adj": p["r_m12"]})
    return results

rank_updates = []
for country, exchanges in RANK_GROUPS.items():
    group = [d for d in all_data if d["exchange"] in exchanges]
    if group:
        res = calc_ranks(group)
        rank_updates.extend(res)
        print(f"  {country}: {len(res)} rankati")

ok = 0
for upd in rank_updates:
    body = {k: v for k, v in upd.items() if k not in ("ticker", "exchange")}
    r = requests.patch(SUPABASE_URL + "/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{upd['ticker']}", "exchange": f"eq.{upd['exchange']}"},
        json=body)
    if r.status_code in (200, 201, 204): ok += 1
print(f"  Rank APAC: {ok}/{len(rank_updates)}")

# Combined rank AP = TSE+SEHK+ASX+KRX+SGX
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"] + d["growth_score"] for d in all_scores]
combined_updates = [{"ticker": d["ticker"], "exchange": d["exchange"],
                     "combined_rank": min(99, pct_rank(sum_arr, d["value_score"] + d["growth_score"]))}
                    for d in all_scores]
ok = 0
for upd in combined_updates:
    _t = upd.pop("ticker"); _e = upd.pop("exchange")
    r = requests.patch(SUPABASE_URL + "/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{_t}", "exchange": f"eq.{_e}"},
        json=upd)
    if r.status_code in (200, 201, 204): ok += 1
print(f"  Combined rank AP: {ok}/{len(combined_updates)}")
ok_rank = ok

# ── INDICI APAC ───────────────────────────────────────────────
print("\n  Aggiornamento indici APAC...")
APAC_INDICES = [
    ("N225.INDX",  "TSE",  "N225",  "Nikkei 225"),
    ("HSI.INDX",   "SEHK", "HSI",   "Hang Seng"),
    ("AXJO.INDX",  "ASX",  "AXJO",  "ASX 200"),
]
ok_idx = 0
FROM_12M = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
for db_ticker, exchange, lt, name in APAC_INDICES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_12M + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200: print(f"  ERR {name}: HTTP {r.status_code}"); continue
        data_raw = r.json()
        if not isinstance(data_raw, list) or not data_raw:
            print(f"  ERR {name}: no data"); continue
        data_sorted = sorted(data_raw, key=lambda x: x["date"])
        valid = [d for d in data_sorted if d.get("close") is not None and float(d["close"]) > 0]
        if not valid: print(f"  ERR {name}: nessun close valido"); continue
        rows = [{"ticker": db_ticker, "exchange": exchange, "date": d["date"],
                 "close": float(d["close"])} for d in valid]
        if rows:
            requests.post(SUPABASE_URL + "/rest/v1/price_history", headers=headers_up, json=rows)
        last     = float(valid[-1]["close"])
        prev     = float(valid[-2]["close"]) if len(valid) >= 2 else None
        change1d = round((last / prev - 1) * 100, 2) if prev and prev != 0 else None
        requests.patch(SUPABASE_URL + "/rest/v1/indices", headers=headers_up,
            params={"ticker": "eq." + db_ticker},
            json={"price": last, "change1d": change1d, "date": valid[-1]["date"]})
        print(f"  {name}: {last:,.2f} ({change1d:+.2f}%)")
        ok_idx += 1
    except Exception as e: print(f"  ERR {name}: {e}")
    time.sleep(0.2)
print(f"  Indici APAC: {ok_idx}/{len(APAC_INDICES)}")

end_time = time_module.time()
log_entry = {"run_date": TODAY, "market": "APAC", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
print(f"\nLog: leeway={ok_prices} fail={fail_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n" + "=" * 60)
print("DAILY APAC LOAD COMPLETATO")
print("=" * 60)
