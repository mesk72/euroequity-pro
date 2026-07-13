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

import os, math, time, time as time_module, requests, random
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
YESTERDAY    = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# Suffissi Leeway per US e TSX
SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
    "BRK.A": "BRK-B.US",  # Leeway copre solo la classe B, più liquida
}

LEEWAY_SUFFIX = {
    "MIL":  ".MI",    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":   ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":   ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":   ".IR",    "AT":    ".VI",
    "LSE":  ".LSE",   "AIM":   ".AIM",   "SWX":  ".SW",
    "OM":   ".ST",    "NGM":   ".ST",    "OB":   ".OL",
    "CPSE": ".CO",
    "US":   ".US",    "TSX":   ".TO",
    "TSE":  ".TSE",   "ASX":   ".AU",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    if exchange == "US":  return ticker.rstrip(".").replace(".", "-") + ".US"
    # Rimuovi punto finale dal ticker (es. UU. -> UU, AO. -> AO)
    ticker_clean = ticker.rstrip(".")
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")


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
        try:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker,exchange,yahoo_ticker,company", "in_universe": "eq.true",
                        "exchange": f"eq.{exchange}", "offset": str(offset), "limit": "1000"},
                timeout=20)
            if not r.text or r.text == "[]": break
            data = r.json()
        except Exception as e:
            print(f"  WARN lettura universo {exchange} offset {offset}: {e}")
            break
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

def safe_post(url, headers, json_data, retries=2):
    """POST con retry: sia su errori di rete SIA su risposte HTTP di errore.
    Prima catturava solo le eccezioni di rete e ignorava lo status code —
    un batch rifiutato da Supabase (400/409/422/5xx) passava per riuscito
    in silenzio, mentre i dati non venivano mai scritti davvero."""
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=json_data, timeout=30)
            if resp.status_code in (200, 201, 204):
                return resp
            print(f"  WARN scrittura rifiutata da Supabase: HTTP {resp.status_code} — {resp.text[:200]}")
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return None
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  WARN salvataggio fallito dopo {retries+1} tentativi: {e}")
            return None

# Ultima data per titolo — query diretta per ticker (indicizzata, veloce,
# affidabile). La versione bulk precedente paginava su tutta la storia
# invece che sull'ultima riga, esaurendosi dopo pochi titoli su universi
# grandi e facendo credere che quasi tutto fosse da riscaricare da zero.
print("  Carico ultime date prezzi...")
last_date_map = {}
for s in all_stocks:
    ticker, exchange = s['ticker'], s['exchange']
    try:
        rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_r,
            params={"select": "date", "ticker": "eq." + ticker, "exchange": "eq." + exchange,
                    "order": "date.desc", "limit": "1"}, timeout=15)
        d = rp.json()
        if isinstance(d, list) and d:
            last_date_map[(ticker, exchange)] = d[0]["date"]
    except Exception:
        pass
print(f"  Ultime date caricate: {len(last_date_map)} titoli")


STATUS_COUNTS = {}
def _fetch_leeway(lt, from_d, to_d):
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20)
            STATUS_COUNTS[resp.status_code] = STATUS_COUNTS.get(resp.status_code, 0) + 1
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else []
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1)); continue
            return None
        except Exception as e:
            STATUS_COUNTS["EXCEPTION:" + type(e).__name__] = STATUS_COUNTS.get("EXCEPTION:" + type(e).__name__, 0) + 1
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return None

WEEK_AGO = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
MAX_ROUNDS = 6
ok_leeway = fail_leeway = 0
price_buf = []
batch_owners = []   # (stock, new_max_date) per ogni riga in price_buf, stesso ordine
pending = list(all_stocks)
random.shuffle(pending)  # evita pattern ripetuti sugli stessi ticker ogni giro

def flush_batch():
    """Scrive il batch corrente e conferma SOLO i titoli il cui scrive e'
    davvero andata a buon fine. Se la scrittura fallisce, i titoli tornano
    in coda per il prossimo giro invece di essere contati come riusciti."""
    global price_buf, batch_owners, ok_leeway
    if not price_buf:
        return []
    resp = safe_post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers_up, price_buf)
    owners_this_batch = batch_owners
    price_buf = []
    batch_owners = []
    if resp is not None:
        seen = set()
        for stock, new_max_date in owners_this_batch:
            key = (stock['ticker'], stock['exchange'])
            if key in seen: continue
            seen.add(key)
            last_date_map[key] = max(new_max_date, last_date_map.get(key, "2021-01-01"))
            ok_leeway += 1
        return []
    else:
        # scrittura fallita davvero (dopo i retry interni di safe_post):
        # questi titoli tornano in coda, NON sono un successo
        return [s for s, _ in owners_this_batch]

for round_num in range(1, MAX_ROUNDS + 1):
    if not pending: break
    print(f"  --- Giro {round_num}/{MAX_ROUNDS}: {len(pending)} titoli da scaricare ---")
    still_pending = []
    for stock in pending:
        ticker, exchange = stock['ticker'], stock['exchange']
        last = last_date_map.get((ticker, exchange), "2021-01-01")
        # Forza sempre almeno 7 giorni di margine (non solo il delta dall'ultima
        # data nota) per recuperare eventuali buchi passati, non solo il giorno
        # mancante di oggi. Nessun titolo viene piu' "saltato" per essere gia' fresco.
        start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        start_dt = min(start_dt, WEEK_AGO)
        lt = leeway_ticker(ticker, exchange)
        data_l = _fetch_leeway(lt, start_dt, TODAY)
        if not data_l:
            still_pending.append(stock)
            continue
        new_max_date = max((row2['date'] for row2 in data_l), default=None)
        if not new_max_date:
            still_pending.append(stock)
            continue
        FRESH_CUTOFF = (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
        if new_max_date <= last and new_max_date < FRESH_CUTOFF:
            still_pending.append(stock)
            continue
        for row2 in data_l:
            adj = row2.get('adjusted_close') or row2.get('close')
            if adj is None: continue
            price_buf.append({"ticker": ticker, "exchange": exchange,
                               "date": row2['date'], "adj_close": float(adj)})
            batch_owners.append((stock, new_max_date))
        if len(price_buf) >= 500:
            write_failed = flush_batch()
            still_pending.extend(write_failed)
        time.sleep(0.5)
    write_failed = flush_batch()  # svuota il resto del batch a fine giro
    still_pending.extend(write_failed)
    pending = still_pending
    if pending and round_num < MAX_ROUNDS:
        pausa = min(10 * round_num, 30)
        print(f"  {len(pending)} ancora falliti — pausa {pausa}s prima del prossimo giro...")
        time.sleep(pausa)

fail_leeway = len(pending)
if pending:
    print(f"  FALLITI DEFINITIVI dopo {MAX_ROUNDS} giri ({fail_leeway}) — diagnosi automatica:")
    for s in pending:
        ticker, exchange = s['ticker'], s['exchange']
        company = s.get('company', '?')
        lt = leeway_ticker(ticker, exchange)
        wide_url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from=2020-01-01&to={TODAY}"
        try:
            wr = requests.get(wide_url, timeout=20)
            wd = wr.json() if wr.status_code == 200 else []
            if isinstance(wd, list) and wd:
                print(f"    {ticker}.{exchange} ({company}): Leeway si ferma al {wd[-1]['date']} — gap dati sul fornitore, non recuperabile da noi")
            else:
                print(f"    {ticker}.{exchange} ({company}): Leeway non ha MAI avuto dati per questo ticker con suffisso {lt} — verificare formato ticker")
        except Exception as e:
            print(f"    {ticker}.{exchange} ({company}): impossibile diagnosticare ({e})")
if price_buf:

    safe_post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers_up, price_buf)
print(f"  Distribuzione codici HTTP/errori su tutte le chiamate: {STATUS_COUNTS}")
print(f"  Prezzi Leeway: ok={ok_leeway} fail={fail_leeway}")
ok_prices = ok_leeway; fail_prices = fail_leeway
# ── 3. LEGGI PREZZI DA prices_eod (chunk 20) ────────────────
print("\n[3/5] Lettura prezzi da prices_eod...")
all_ph = defaultdict(list)
for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        offset_p = 0
        from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        while True:
            try:
                rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_r,
                    params={"select": "ticker,date,adj_close",
                            "exchange": f"eq.{exchange}",
                            "ticker": f"in.({','.join(chunk)})",
                            "date": f"gte.{from_400d}",
                            "order": "ticker,date.desc",
                            "limit": "1000", "offset": str(offset_p)},
                    timeout=20)
                batch = rp.json()
            except Exception as e:
                print(f"  WARN lettura prezzi chunk {exchange} offset {offset_p}: {e}")
                break
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
SPLIT_THRESHOLD_PCT = 20
split_suspects = []
for stock in all_stocks:
    ticker = stock['ticker']; exchange = stock['exchange']
    data = all_ph.get((ticker, exchange), [])
    if len(data) < 2: fail += 1; continue
    last_px   = data[0]['close']
    last_date = datetime.strptime(data[0]['date'], "%Y-%m-%d")
    chg1d = round((data[0]['close'] / data[1]['close'] - 1) * 100, 4)
    if abs(chg1d) > SPLIT_THRESHOLD_PCT:
        split_suspects.append((ticker, exchange, chg1d))

    def mom_cal(days):
        target  = last_date - timedelta(days=days)
        closest = min(data, key=lambda x: abs((datetime.strptime(x['date'], "%Y-%m-%d") - target).days))
        if closest['close'] and closest['close'] != 0:
            return round(last_px / closest['close'] - 1, 6)
        return None

    def mom1w_trading():
        # 1w = esattamente 5 giorni di CONTRATTAZIONE fa (come Yahoo Finance
        # "5G"), non "7 giorni di calendario piu' vicino" — le due
        # convenzioni divergono quando cadono festivita' di mercato che
        # spostano il conteggio in modo diverso da paese a paese.
        if len(data) < 6: return None
        base = data[5]['close']
        if base and base != 0:
            return round(last_px / base - 1, 6)
        return None

    mom_updates.append({
        "ticker": ticker, "exchange": exchange,
        "mom1w": mom1w_trading(), "mom1m": mom_cal(30),
        "mom6m": mom_cal(182), "mom12m": mom_cal(365),
        "change1d": chg1d, "price": last_px,
    })
    ok += 1

# Se un titolo varia di oltre SPLIT_THRESHOLD_PCT in un giorno, probabile
# stock split non segnalato da Leeway: ricarica tutto lo storico a 5 anni.
if split_suspects:
    print(f"\n  Rilevati {len(split_suspects)} possibili stock split (variazione 1gg > {SPLIT_THRESHOLD_PCT}%): ricarico 5 anni di storico...")
    FROM_5Y = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
    mom_by_key = {(u["ticker"], u["exchange"]): u for u in mom_updates}
    for ticker, exchange, old_chg in split_suspects:
        lt = leeway_ticker(ticker, exchange)
        url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
        try:
            resp = requests.get(url, timeout=20)
            data_l = resp.json() if resp.status_code == 200 else []
            if not isinstance(data_l, list) or not data_l:
                print(f"    {ticker}.{exchange}: nessun dato storico da Leeway (variazione era {old_chg}%), salto")
                continue
            requests.delete(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up,
                params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})
            new_rows = []
            for row2 in data_l:
                adj = row2.get('adjusted_close') or row2.get('close')
                if adj is None: continue
                new_rows.append({"ticker": ticker, "exchange": exchange,
                                  "date": row2['date'], "adj_close": float(adj)})
            for i in range(0, len(new_rows), 500):
                requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=new_rows[i:i+500])
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

                def mom1w_trading2():
                    if len(new_sorted) < 6: return None
                    base = new_sorted[5]["adj_close"]
                    if base and base != 0:
                        return round(last_px2 / base - 1, 6)
                    return None

                key = (ticker, exchange)
                if key in mom_by_key:
                    mom_by_key[key].update({
                        "mom1w": mom1w_trading2(), "mom1m": mom_cal2(30),
                        "mom6m": mom_cal2(182), "mom12m": mom_cal2(365),
                        "change1d": new_chg1d, "price": last_px2,
                    })
                print(f"    {ticker}.{exchange}: ricaricato ({len(new_rows)} righe), variazione ricalcolata {new_chg1d}%")
        except Exception as e:
            print(f"    {ticker}.{exchange}: errore ricarica — {e}")
        time.sleep(0.3)

for i in range(0, len(mom_updates), 100):
    safe_post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers_up, mom_updates[i:i+100])
print(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

# ── 5. RANK US+CA ────────────────────────────────────────────
print("\n[5/5] Ricalcolo rank US+CA...")
all_data = []
offset = 0
# in_universe vive in stocks non in fundamentals — usa universe_keys
universe_keys = {(s["ticker"], s["exchange"]) for s in all_stocks}
while True:
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
            params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                    "exchange": "in.(US,TSX)",
                    "offset": str(offset), "limit": "1000"},
            timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  WARN lettura fundamentals per rank offset {offset}: {e}")
        break
    if not isinstance(data, list) or not data: break
    all_data.extend([d for d in data if (d["ticker"], d["exchange"]) in universe_keys])
    offset += 1000
    if len(data) < 1000: break
print(f"  Fundamentals: {len(all_data)}")

# USA mom_updates (calcolati sui prezzi aggiornati) non all_data (dati vecchi DB)
mom1w_map = {(d['ticker'], d['exchange']): d.get('mom1w') for d in mom_updates}
mom1m_map = {(d['ticker'], d['exchange']): d.get('mom1m') for d in mom_updates}
# Aggiungi anche mom6m e mom12m aggiornati
mom6m_map  = {(d['ticker'], d['exchange']): d.get('mom6m')  for d in mom_updates}
mom12m_map = {(d['ticker'], d['exchange']): d.get('mom12m') for d in mom_updates}

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
        key = (d['ticker'], d['exchange'])
        # Usa valori aggiornati da mom_updates, non quelli vecchi di fundamentals
        m6  = mom6m_map.get(key, d.get('mom6m'))
        m12 = mom12m_map.get(key, d.get('mom12m'))
        m1w = mom1w_map.get(key, d.get('mom1w'))
        m1m = mom1m_map.get(key, d.get('mom1m'))
        if m6  is not None and m1w is not None: mom6_adj_g.append(m6 - m1w)
        if m12 is not None and m1m is not None: mom12_adj_g.append(m12 - m1m)
    pre = []
    for d in group:
        key  = (d['ticker'], d['exchange'])
        m6   = mom6m_map.get(key, d.get('mom6m'))
        m12  = mom12m_map.get(key, d.get('mom12m'))
        m1w  = mom1w_map.get(key, d.get('mom1w'))
        m1m  = mom1m_map.get(key, d.get('mom1m'))
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
# Scrittura BATCH invece di un PATCH per ogni titolo — la versione precedente
# faceva migliaia di chiamate HTTP individuali, causa primaria dei run che
# non riuscivano a completare in tempo utile ogni notte.
for i in range(0, len(rank_updates), 200):
    batch = rank_updates[i:i+200]
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=batch, timeout=30)
        if r.status_code in (200, 201, 204):
            ok += len(batch)
        else:
            print(f"  WARN batch rank: HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"  WARN batch rank: {e}")
print(f"  Rank US+CA: {ok}/{len(rank_updates)}")

# Combined rank NA = US+TSX insieme
try:
    requests.patch(SUPABASE_URL + "/rest/v1/fundamentals",
        headers={**headers_up, "Prefer": "return=minimal"},
        params={"exchange": "in.(US,TSX)"},
        json={"combined_rank": None}, timeout=30)
except Exception as e:
    print(f"  WARN reset combined_rank: {e}")
all_scores = [d for d in rank_updates if d.get('value_score') is not None and d.get('growth_score') is not None]
comb_arr   = [d['value_score'] + d['growth_score'] for d in all_scores]
combined_updates = [{"ticker": d['ticker'], "exchange": d['exchange'],
                     "combined_rank": min(99, int(round(pct_rank(comb_arr, d['value_score'] + d['growth_score']))))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 200):
    batch = combined_updates[i:i+200]
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=batch, timeout=30)
        if r.status_code in (200, 201, 204):
            ok += len(batch)
        else:
            print(f"  WARN batch combined: HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"  WARN batch combined: {e}")
print(f"  Combined rank NA (US+TSX): {ok}/{len(combined_updates)}")
ok_rank = ok

# ── INDICI NORD AMERICA ──────────────────────────────────────
print("\n  Aggiornamento indici Nord America...")
NA_INDICES = [
    ("GSPC.INDX",   "US",  "GSPC",    "S&P 500"),
    ("IXIC.INDX",   "US",  "IXIC",    "Nasdaq"),
    ("DJI.INDX",    "US",  "DJI",     "Dow Jones"),
    ("GSPTSE.INDX", "TSX", "GSPTSE",  "TSX"),
]
ok_idx = 0
FROM_12M = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
for db_ticker, exchange, lt, name in NA_INDICES:
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_12M}&to={TODAY}"
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
        last  = float(valid[-1]["close"])
        prev  = float(valid[-2]["close"]) if len(valid) >= 2 else None
        change1d = round((last / prev - 1) * 100, 2) if prev and prev != 0 else None
        requests.patch(SUPABASE_URL + "/rest/v1/indices", headers=headers_up,
            params={"ticker": f"eq.{db_ticker}"},
            json={"price": last, "change1d": change1d, "date": valid[-1]["date"]})
        print(f"  {name}: {last:,.2f} ({change1d:+.2f}%)")
        ok_idx += 1
    except Exception as e: print(f"  ERR {name}: {e}")
    time.sleep(0.2)
print(f"  Indici NA: {ok_idx}/{len(NA_INDICES)}")

end_time = time_module.time()
log_entry = {"run_date": TODAY, "market": "US+CA", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
try:
    requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry], timeout=15)
except Exception as e:
    print(f"  WARN salvataggio daily_log: {e}")
print(f"\nLog: leeway={ok_prices} fail={fail_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
print("\n" + "=" * 60)
print("DAILY US+CA LOAD COMPLETATO")
print("=" * 60)
