# ============================================================
# FORWARDALPHA — DAILY EU LOAD (YAHOO FINANCE)
# Da eseguire ogni giorno alle 19:00 UTC (21:00 CET)
# Prezzi EOD da Yahoo Finance invece di Leeway
# Copre tutti i mercati EU
# ============================================================

import os, math, time, time as time_module, requests
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "python-dateutil", "--break-system-packages", "-q"])
    from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from collections import defaultdict
import yfinance as yf

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

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
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
    # Rimuovi punto finale dal ticker (es. UU. -> UU, AO. -> AO)
    ticker_clean = ticker.rstrip(".")
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")


start_time = time_module.time()
print("=" * 60)
print("FORWARDALPHA DAILY EU LOAD — " + TODAY)
print("=" * 60)

# ── 1. CARICA UNIVERSO EU ────────────────────────────────────
print("\n[1/5] Caricamento universo EU...")
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker", "in_universe": "eq.true",
                "exchange": "not.in.(US,TSX,TSE,SEHK,ASX)",
                "offset": str(offset), "limit": "1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print("  Universo EU: " + str(len(all_stocks)) + " titoli")

by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s["exchange"]].append(s["ticker"])

# ── 2. SCARICA PREZZI EOD DA YAHOO FINANCE ──────────────────
print("\n[2/5] Download prezzi EOD da Yahoo Finance...")

# Suffissi Yahoo per exchange
YAHOO_SUFFIX = {
    "MIL": ".MI", "XETRA": ".DE", "PA": ".PA", "AS": ".AS",
    "MC": ".MC", "BR": ".BR", "LS": ".LS", "VI": ".VI",
    "HE": ".HE", "IR": ".IR", "AT": ".VI",
    "LSE": ".L",  "AIM": ".L",  "SWX": ".SW",
    "OM": ".ST",  "NGM": ".ST", "OB": ".OL",
    "CPSE": ".CO",
}

SPECIAL_YAHOO = {
    "ROG": "ROG.SW", "BP.": "BP.L", "RR.": "RR.L",
    "BT.A": "BT-A.L", "BA.": "BA.L", "NG.": "NG.L",
}

def yahoo_ticker(ticker, exchange):
    if ticker in SPECIAL_YAHOO: return SPECIAL_YAHOO[ticker]
    if exchange in ("OM", "NGM", "CPSE"):
        return ticker.replace(" ", "-") + YAHOO_SUFFIX.get(exchange, "")
    if exchange == "BR":
        return ticker.replace(".", "") + YAHOO_SUFFIX.get(exchange, "")
    return ticker.rstrip(".") + YAHOO_SUFFIX.get(exchange, "")

ok_yf = fail_yf = 0
price_buf = []

# Prima controlla ultima data per ogni titolo
last_dates = {}
for stock in all_stocks:
    rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date", "ticker": "eq." + stock["ticker"],
                "exchange": "eq." + stock["exchange"],
                "order": "date.desc", "limit": "1"})
    row = rp.json()
    last_dates[(stock["ticker"], stock["exchange"])] = row[0]["date"] if isinstance(row, list) and row else "2020-01-01"

# Scarica per exchange in chunk da 150 titoli
import random
for exchange, tickers in by_exchange.items():
    CHUNK = 150
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        # Costruisci lista yahoo tickers
        stock_map = {s["ticker"]: s for s in all_stocks if s["exchange"] == exchange and s["ticker"] in chunk}
        ytickers = []
        ticker_map = {}  # yahoo_ticker → (ticker, exchange)
        for tk in chunk:
            # Salta se già aggiornato oggi
            if last_dates.get((tk, exchange), "") >= TODAY:
                ok_yf += 1
                continue
            s = stock_map.get(tk, {})
            # Usa yahoo_ticker dal DB se disponibile
            yt = s.get("yahoo_ticker") or yahoo_ticker(tk, exchange)
            ytickers.append(yt)
            ticker_map[yt] = (tk, exchange)

        if not ytickers:
            continue

        # Data di partenza = la più vecchia tra i titoli del chunk
        start_dates = [last_dates.get((ticker_map[yt][0], exchange), "2020-01-01") for yt in ytickers]
        start_dt = min(start_dates)
        # Aggiungi 1 giorno
        from datetime import datetime as dt
        start_dt = (dt.strptime(start_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            data_yf = yf.download(
                tickers=" ".join(ytickers),
                start=start_dt,
                end=TODAY,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if data_yf.empty:
                fail_yf += len(ytickers)
                continue

            # Estrai Adj Close (con auto_adjust=True si chiama Close)
            if len(ytickers) == 1:
                closes = data_yf[["Close"]].rename(columns={"Close": ytickers[0]})
            else:
                closes = data_yf["Close"] if "Close" in data_yf.columns else data_yf

            for yt in ytickers:
                if yt not in closes.columns:
                    fail_yf += 1
                    continue
                tk, ex = ticker_map[yt]
                last = last_dates.get((tk, ex), "2020-01-01")
                series = closes[yt].dropna()
                for date_idx, price in series.items():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    if date_str <= last: continue
                    price_buf.append({"ticker": tk, "exchange": ex,
                                      "date": date_str, "adj_close": round(float(price), 6)})
                ok_yf += 1

        except Exception as e:
            print(f"  Errore chunk {exchange} {i}: {e}")
            fail_yf += len(ytickers)

        if len(price_buf) >= 500:
            requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
            price_buf = []

        # Pausa random tra chunk
        time.sleep(random.uniform(3.0, 7.0))

if price_buf:
    requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
print("  Prezzi Yahoo: ok=" + str(ok_yf) + " fail=" + str(fail_yf))
ok_prices = ok_yf; fail_prices = fail_yf

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
print("  Prezzi caricati: " + str(len(all_ph)) + " titoli")

# ── 4. MOMENTUM ──────────────────────────────────────────────
print("\n[4/5] Calcolo momentum...")
ok = fail = 0
mom_updates = []
for stock in all_stocks:
    ticker = stock["ticker"]; exchange = stock["exchange"]
    data = all_ph.get((ticker, exchange), [])
    if len(data) < 2: fail += 1; continue
    last_px   = data[0]["close"]
    last_date = datetime.strptime(data[0]["date"], "%Y-%m-%d")
    chg1d = round(data[0]["close"] / data[1]["close"] - 1, 6)

    def mom_new_weeks(trading_days_back):
        if len(data) <= trading_days_back: return None
        ref_price = data[trading_days_back]["close"]
        if ref_price and ref_price != 0:
            return round(last_px / ref_price - 1, 6)
        return None

    def mom_new_months(months):
        target = last_date.date() - relativedelta(months=months)
        target_plus1 = target + timedelta(days=1)
        candidates = [p for p in data if p["date"] >= target_plus1.isoformat()]
        if not candidates: return None
        ref = min(candidates, key=lambda p: p["date"])
        if ref["close"] and ref["close"] != 0:
            return round(last_px / ref["close"] - 1, 6)
        return None

    mom_updates.append({"ticker": ticker, "exchange": exchange,
                         "mom1w": mom_new_weeks(4), "mom1m": mom_new_months(1),
                         "mom6m": mom_new_months(6), "mom12m": mom_new_months(12),
                         "change1d": chg1d, "price": last_px})
    ok += 1

for i in range(0, len(mom_updates), 100):
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=mom_updates[i:i+100])
print("  Momentum ok=" + str(ok) + " fail=" + str(fail))
ok_momentum = ok

# ── 5. FX ────────────────────────────────────────────────────
print("\n  Aggiornamento FX...")
FX_PAIRS = {"EURGBP=X":"EURGBP","EURCHF=X":"EURCHF","EURSEK=X":"EURSEK",
            "EURNOK=X":"EURNOK","EURDKK=X":"EURDKK","EURUSD=X":"EURUSD","GBPUSD=X":"GBPUSD"}
fx_rates = {"date": TODAY}
for pair_sym, pair_name in FX_PAIRS.items():
    try:
        info = yf.Ticker(pair_sym).info
        fx_rates[pair_name] = info.get("regularMarketPrice") or info.get("previousClose")
    except: pass
    time.sleep(0.2)
requests.post(SUPABASE_URL + "/rest/v1/fx_rates", headers=headers_up, json=[fx_rates])
print("  FX salvati")

# ── 6. RANK EU ───────────────────────────────────────────────
print("\n[5/5] Ricalcolo rank EU...")
all_data = []
offset = 0
# in_universe vive in stocks non in fundamentals
# Usa i ticker già caricati in all_stocks come filtro
universe_keys = {(s["ticker"], s["exchange"]) for s in all_stocks}
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange": "not.in.(US,TSX,TSE,SEHK,ASX)",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not isinstance(data, list) or not data: break
    # Filtra solo i titoli in universe
    all_data.extend([d for d in data if (d["ticker"], d["exchange"]) in universe_keys])
    offset += 1000
    if len(data) < 1000: break
print("  Fundamentals: " + str(len(all_data)))

# Mom maps da mom_updates (prezzi appena scaricati) NON dal DB vecchio
mom1w_map  = {(d["ticker"], d["exchange"]): d.get("mom1w")  for d in mom_updates}
mom1m_map  = {(d["ticker"], d["exchange"]): d.get("mom1m")  for d in mom_updates}
mom6m_map  = {(d["ticker"], d["exchange"]): d.get("mom6m")  for d in mom_updates}
mom12m_map = {(d["ticker"], d["exchange"]): d.get("mom12m") for d in mom_updates}

RANK_GROUPS = {
    "ITA": ["MIL"], "DEU": ["XETRA"], "FRA": ["PA"], "GBR": ["LSE"],
    "SWE": ["OM"],  "NOR": ["OB"],    "CHE": ["SWX"], "NLD": ["AS"],
    "BEL": ["BR"],  "FIN": ["HE"],    "ESP": ["MC"],  "DNK": ["CPSE"],
}
NO_RANK = {"AT", "VI", "IR", "NGM", "AIM", "LS"}  # LS: titoli insufficienti

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
        print("  " + country + ": " + str(len(res)) + " rankati")

ranked_exchanges = set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked = [d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked:
    rank_updates.extend(calc_ranks(unranked))

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
print("  Rank EU: " + str(ok) + "/" + str(len(rank_updates)))

# Combined rank EU
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"] + d["growth_score"] for d in all_scores]
combined_updates = [{"ticker": d["ticker"], "exchange": d["exchange"],
                     "combined_rank": min(99, pct_rank(sum_arr, d["value_score"] + d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
print("  Combined rank EU: " + str(ok) + "/" + str(len(combined_updates)))
ok_rank = ok

# ── INDICI EU ────────────────────────────────────────────────
print("\n  Aggiornamento indici EU...")
EU_INDICES = [
    ("GDAXI.INDX", "XETRA", "DAX",      "DAX"),
    ("FCHI.INDX",  "PA",    "FCHI",     "CAC 40"),
    ("AEX.INDX",   "AS",    "AEX",      "AEX"),
    ("IBEX.INDX",  "MC",    "IBEX",     "IBEX 35"),
    ("BFX.INDX",   "BR",    "BFX",      "BEL 20"),
    # ("FTSE.INDX", "LSE", "FTSE", "FTSE 100"),  # ticker Leeway da verificare
    ("SSMI.INDX",  "SWX",   "SMI",      "SMI"),
    ("OMXS30.INDX","OM",    "OMXS30",   "OMX Stockholm"),
    ("OMXC25.INDX","CPSE",  "C25",      "OMX Copenhagen"),
    ("ATX.INDX",   "VI",    "ATX",      "ATX"),
    # ("ISEQ.INDX", "IR", "IEX", "ISEQ"),  # ticker Leeway da verificare
    ("STOXX50E.INDX","EZ",  "SX5E",     "Euro Stoxx 50"),
    ("SXXP.INDX",  "EZ",    "SXXP",     "STOXX 600"),
    ("OMXH25.INDX", "HE",   "HEX",      "OMX Helsinki"),
    # ("FTSEMIB.MI", "MIL", "MIB", "FTSE MIB"),  # ticker Leeway da verificare
    ("PSI20.INDX", "LS",    "PSI",      "PSI 20"),
]
ok_idx = 0
FROM_12M = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
for db_ticker, exchange, lt, name in EU_INDICES:
    url = LEEWAY_BASE + "/historicalquotes/" + lt + "?apitoken=" + LEEWAY_KEY + "&from=" + FROM_12M + "&to=" + TODAY
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200: print("  ERR " + name + ": HTTP " + str(r.status_code)); continue
        data_raw = r.json()
        if not isinstance(data_raw, list) or not data_raw:
            print("  ERR " + name + ": no data"); continue
        data_sorted = sorted(data_raw, key=lambda x: x["date"])
        valid = [d for d in data_sorted if d.get("close") is not None and float(d["close"]) > 0]
        if not valid: print("  ERR " + name + ": nessun close valido"); continue
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
        print("  " + name + ": " + str(round(last, 2)) + " (" + str(change1d) + "%)")
        ok_idx += 1
    except Exception as e: print("  ERR " + name + ": " + str(e))
    time.sleep(0.2)
print("  Indici EU: " + str(ok_idx) + "/" + str(len(EU_INDICES)))

end_time = time_module.time()
log_entry = {"run_date": TODAY, "market": "EU", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
print("\nLog: leeway=" + str(ok_prices) + " fail=" + str(fail_prices) + " momentum=" + str(ok_momentum) + " rank=" + str(ok_rank) + " durata=" + str(int(end_time-start_time)) + "s")
print("\n" + "=" * 60)
print("DAILY EU LOAD COMPLETATO")
print("=" * 60)
