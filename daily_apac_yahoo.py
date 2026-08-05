# ============================================================
# FORWARDALPHA — DAILY APAC LOAD
# Da eseguire ogni giorno alle 09:00 CET (dopo chiusura Asia)
# Copre: TSE (Giappone), SEHK (Hong Kong), ASX (Australia)
# ============================================================

import os, math, time, time as time_module, requests
import pandas as pd
import yfinance as yf
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "python-dateutil", "--break-system-packages", "-q"])
    from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from collections import defaultdict

# ── LOCK ANTI-DOPPIA-ESECUZIONE ──────────────────────────────
# FIX 29/7/2026: daily_log mostrava piu' righe identiche nello stesso
# giorno per lo stesso mercato (possibile sovrapposizione tra cron
# Vercel e dispatch manuali) — spreco di chiamate Yahoo/Supabase e
# rischio di rate limiting. Prima di iniziare, controlla se c'e' GIA'
# un'altra esecuzione di QUESTO STESSO workflow in corso (diversa dalla
# mia, tramite GH_RUN_ID) — se si', esce subito invece di duplicare il
# lavoro. Non richiede una nuova tabella: usa direttamente l'API di
# GitHub Actions. Se il controllo stesso fallisce (token mancante,
# rete), procede comunque per non bloccare l'esecuzione per un motivo
# secondario.
_gh_token = os.environ.get("GH_TOKEN", "")
_gh_repo = os.environ.get("GH_REPO", "")
_gh_run_id = os.environ.get("GH_RUN_ID", "")
_gh_workflow = os.environ.get("GH_WORKFLOW", "")
if _gh_token and _gh_repo and _gh_workflow:
    try:
        _r = requests.get(
            f"https://api.github.com/repos/{_gh_repo}/actions/workflows/{_gh_workflow}/runs",
            headers={"Authorization": f"token {_gh_token}", "Accept": "application/vnd.github+json"},
            params={"status": "in_progress", "per_page": "10"}, timeout=15)
        _runs = _r.json().get("workflow_runs", [])
        _others = [x for x in _runs if str(x.get("id")) != str(_gh_run_id)]
        if _others:
            print(f"LOCK: un'altra esecuzione di {_gh_workflow} e' gia' in corso (run {_others[0]['id']}) - esco per evitare duplicati.")
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as _e:
        print(f"LOCK: controllo fallito ({_e}), procedo comunque.")

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
# Margine di 2 giorni per il download Yahoo — 'end' e' ESCLUSIVO in
# yfinance, e se lo script gira poco prima della mezzanotte UTC, TODAY
# potrebbe risultare "ieri" rispetto al vero giorno di mercato, tagliando
# fuori l'ultimo giorno disponibile (bug reale riscontrato il 23/7/2026).
END_FOR_DOWNLOAD = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
TODAY_DT     = datetime.now()

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# ── BLOCCO DI SICUREZZA: si scrivono solo sedute concluse ────
# FIX 31/7/2026: yfinance, se interrogato a mercato APERTO, restituisce
# anche una barra PARZIALE del giorno in corso, col prezzo dell'istante
# invece della chiusura. Una volta scritta in prices_eod diventa
# indistinguibile da una chiusura vera e falsa prezzi, rendimenti e di
# conseguenza i punteggi.
# Caso reale che ha portato a questo controllo: ~380 titoli europei con un
# prezzo datato 30/07/2026 che Yahoo non conferma come chiusura (es.
# AKTIA.HE a 11,96 contro 11,30 del 29/07), scritti quasi certamente da
# un'esecuzione manuale delle 09:06 a mercati aperti durante il debug.
# Regola: una barra datata D si accetta solo dopo l'orario limite di
# chiusura di D. Margine volutamente abbondante, valido anche con l'ora
# solare: meglio saltare una barra e riprenderla alla prossima esecuzione
# che scriverne una sbagliata. Le esecuzioni programmate non perdono nulla
# (girano a mercati chiusi da ore).
ORA_LIMITE_UTC = 10  # Asia-Pacifico: la piu' tarda e' Singapore, 17:00 SGT = 09:00 UTC
saltate_seduta_aperta = 0

def seduta_conclusa(date_str):
    """True se la seduta di quella data e' sicuramente gia' chiusa."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return False
    return datetime.utcnow() >= d.replace(hour=ORA_LIMITE_UTC, minute=0, second=0)


# LOCK ANTI-DOPPIA-ESECUZIONE (solo per trigger automatici) - FIX 30/7/2026:
# EU/US sono girati 3 volte in una notte (Vercel cron + cron nativo GitHub
# aggiunto oggi + eventuali trigger manuali). 'concurrency' nel workflow
# evita sovrapposizioni PARALLELE ma non esecuzioni sequenziali multiple
# nello stesso giorno. Qui si salta SOLO se il trigger e' un cron
# automatico (schedule) E oggi risulta gia' un'esecuzione completata per
# questo mercato - i trigger manuali (workflow_dispatch, usati per
# debug/riparazioni) restano SEMPRE permessi senza restrizioni.
if os.environ.get("GITHUB_EVENT_NAME") == "schedule":
    _lock_check = requests.get(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_r,
        params={"select": "duration_seconds", "run_date": "eq." + TODAY, "market": "eq.APAC", "limit": "1"})
    _lock_rows = _lock_check.json()
    if isinstance(_lock_rows, list) and _lock_rows and _lock_rows[0].get("duration_seconds"):
        print(f"LOCK: gia' un'esecuzione completata oggi per APAC (run_date={TODAY}). Esco per evitare doppio run automatico.")
        exit(0)

_log_buffer = []
def log(msg):
    print(msg)
    _log_buffer.append(str(msg))
    try:
        requests.post(SUPABASE_URL + "/rest/v1/script_logs", headers=headers_up,
            json={"script_name": "daily_apac_yahoo", "log_text": "\n".join(_log_buffer)},
            timeout=10)
    except Exception:
        pass

def leeway_ticker(ticker, exchange):
    if exchange == "TSE":
        return ticker + ".TSE"         # es. 7203.TSE
    elif exchange == "SEHK":
        return ticker.zfill(4) + ".HK" # es. 0700.HK
    elif exchange == "ASX":
        return ticker + ".AU"          # es. BHP.AU
    return ticker

start_time = time_module.time()
log("=" * 60)
log(f"FORWARDALPHA DAILY APAC LOAD — {TODAY}")
log("=" * 60)

# ── 1. CARICA UNIVERSO APAC ──────────────────────────────────
log("\n[1/5] Caricamento universo APAC...")
all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker,primary_exchange", "in_universe": "eq.true",
                "exchange": "in.(TSE,SEHK,ASX,KRX,SGX)",  # KRX/SGX riportati qui: il vecchio
                # sistema Leeway dedicato (daily_apac.py/.yml) fallisce
                # silenziosamente da tempo (Leeway dismesso), lasciando
                # 500 titoli senza aggiornamenti quotidiani senza che
                # nessun errore fosse visibile (28/7/2026).
                # FIX 29/7/2026: order esplicito - senza, Postgres non
                # garantisce un ordine stabile tra esecuzioni diverse,
                # quindi la composizione dei chunk da 150 titoli poteva
                # cambiare ogni volta. Se un chunk incontra un problema
                # (rate limit, blip di rete su un batch Yahoo), i titoli
                # che ne risentono cambiavano run dopo run in modo
                # imprevedibile (causa sospetta di BHP e altri titoli ASX
                # bloccati in modo apparentemente casuale).
                "order": "ticker.asc",
                "offset": str(offset), "limit": "1000"})
    if not r.text or r.text == "[]": break
    try: data = r.json()
    except: break
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
log(f"  Universo APAC: {len(all_stocks)} titoli")

by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s["exchange"]].append(s["ticker"])

# ── 2. SCARICA PREZZI EOD DA YAHOO FINANCE ──────────────────
log("\n[2/5] Download prezzi EOD da Yahoo Finance...")

YAHOO_SUFFIX = {
    "TSE":  "",    # Yahoo: 7203.T, 9984.T
    "SEHK": ".HK", # Yahoo: 0700.HK
    "ASX":  ".AX", # Yahoo: BHP.AX (non .AU!)
    "KRX":  ".KS", # Yahoo: 005930.KS (Samsung)
    "SGX":  ".SI", # Yahoo: D05.SI (DBS)
}

def yahoo_ticker(ticker, exchange, primary_ex=""):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "TSE":
        # Tokyo: rimuovi zeri iniziali extra, aggiungi .T
        return ticker.lstrip("0") + ".T" if ticker.isdigit() else ticker + ".T"
    if exchange == "KRX":
        # Yahoo: KOSPI = .KS, KOSDAQ = .KQ
        return ticker.lstrip("A") + (".KQ" if primary_ex == "KOSDAQ" else ".KS")
    if exchange == "SGX": return ticker + ".SI"
    if exchange in ("TSX",): return ticker.replace(".", "-") + ".TO"
    return ticker + YAHOO_SUFFIX.get(exchange, "")

ok_yf = fail_yf = 0
price_buf = []
import random

# Ultima data per titolo
last_dates = {}
# Una query per MERCATO (non per singolo titolo, che con migliaia di
# titoli faceva scadere il timeout prima del vero download - causa
# reale del prezzo fermo di giorni, 23-24/7/2026). Stima la data piu'
# recente per ciascun mercato distinto nell'universo, poi la usa per
# tutti i suoi titoli - l'upsert successivo sovrascrive senza danni se
# qualche titolo avesse per caso uno storico diverso.
distinct_exchanges = sorted(set(s["exchange"] for s in all_stocks))
global_last_by_exchange = {}
for ex in distinct_exchanges:
    rg = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date", "exchange": "eq." + ex, "order": "date.desc", "limit": "1"})
    row = rg.json()
    most_recent = row[0]["date"] if isinstance(row, list) and row else "2020-01-01"
    safety_dt = (datetime.strptime(most_recent, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
    global_last_by_exchange[ex] = safety_dt
    log(f"  Data piu' recente nel mercato {ex}: {most_recent} — uso {safety_dt} come base (margine di sicurezza)")
for stock in all_stocks:
    last_dates[(stock["ticker"], stock["exchange"])] = global_last_by_exchange.get(stock["exchange"], "2020-01-01")

# Download per exchange in chunk da 150
for exchange, tickers in by_exchange.items():
    CHUNK = 150
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        stock_map = {s["ticker"]: s for s in all_stocks if s["exchange"] == exchange and s["ticker"] in chunk}
        ytickers = []
        ticker_map = {}
        for tk in chunk:
            if last_dates.get((tk, exchange), "") >= TODAY:
                ok_yf += 1; continue
            s = stock_map.get(tk, {})
            yt = s.get("yahoo_ticker") or yahoo_ticker(tk, exchange, s.get("primary_exchange") or "")
            ytickers.append(yt)
            ticker_map[yt] = (tk, exchange)
        if not ytickers: continue

        start_dates = [last_dates.get((ticker_map[yt][0], exchange), "2020-01-01") for yt in ytickers]
        start_dt = min(start_dates)
        from datetime import datetime as dt2
        start_dt = (dt2.strptime(start_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            data_yf = yf.download(
                tickers=" ".join(ytickers), start=start_dt, end=END_FOR_DOWNLOAD,
                interval="1d", auto_adjust=True, progress=False, threads=True,
            )
            if data_yf.empty: fail_yf += len(ytickers); continue

            # Stesso fix robusto applicato a US (26/7/2026) — un solo
            # ticker con formato dati anomalo poteva far perdere l'intero
            # gruppo di 150 titoli senza nessun errore visibile.
            if len(ytickers) == 1:
                closes = data_yf[["Close"]].rename(columns={"Close": ytickers[0]})
            elif isinstance(data_yf.columns, pd.MultiIndex):
                if "Close" in data_yf.columns.get_level_values(0):
                    closes = data_yf["Close"]
                elif "Close" in data_yf.columns.get_level_values(1):
                    closes = data_yf.xs("Close", axis=1, level=1)
                else:
                    closes = None
            elif "Close" in data_yf.columns:
                closes = data_yf[["Close"]].rename(columns={"Close": ytickers[0]})
            else:
                closes = None

            if closes is None or not hasattr(closes, "columns"):
                raise ValueError("formato dati Yahoo non riconosciuto per questo chunk")

            for yt in ytickers:
                if yt not in closes.columns: fail_yf += 1; continue
                tk, ex = ticker_map[yt]
                last = last_dates.get((tk, ex), "2020-01-01")
                col_valid = closes[yt].dropna()
                # DIAGNOSTICA 29/7/2026: nessuna eccezione veniva sollevata
                # se un titolo, DENTRO un chunk bulk altrimenti riuscito,
                # tornava con dati fermi a piu' di 2 giorni fa (es. BHP
                # fermo mentre 149 titoli-fratelli nello stesso chunk
                # arrivavano fino a oggi) — ok_yf veniva comunque
                # incrementato, nessun log, nessun modo di accorgersene
                # senza controllare manualmente titolo per titolo.
                if len(col_valid) > 0:
                    col_last = col_valid.index.max().strftime("%Y-%m-%d")
                    days_behind = (datetime.strptime(TODAY, "%Y-%m-%d") - datetime.strptime(col_last, "%Y-%m-%d")).days
                    if days_behind > 2:
                        log(f"    ATTENZIONE {tk}.{ex}: dati Yahoo fermi al {col_last} ({days_behind}gg fa) dentro un chunk altrimenti riuscito")
                for date_idx, price in col_valid.items():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    if date_str <= last: continue
                    if not seduta_conclusa(date_str):
                        saltate_seduta_aperta += 1
                        continue
                    price_buf.append({"ticker": tk, "exchange": ex, "date": date_str, "adj_close": round(float(price), 6)})
                ok_yf += 1
        except Exception as e:
            log(f"  Chunk {exchange} {i} fallito ({e}), riprovo singolarmente...")
            for yt in ytickers:
                try:
                    single = yf.download(yt, start=start_dt, end=END_FOR_DOWNLOAD,
                        interval="1d", auto_adjust=True, progress=False)
                    if single.empty or "Close" not in single.columns:
                        fail_yf += 1; continue
                    tk, ex = ticker_map[yt]
                    last = last_dates.get((tk, ex), "2020-01-01")
                    for date_idx, price in single["Close"].dropna().items():
                        date_str = date_idx.strftime("%Y-%m-%d")
                        if date_str <= last: continue
                        if not seduta_conclusa(date_str):
                            saltate_seduta_aperta += 1
                            continue
                        price_buf.append({"ticker": tk, "exchange": ex, "date": date_str, "adj_close": round(float(price), 6)})
                    ok_yf += 1
                except Exception as e2:
                    log(f"    Fallito anche singolarmente: {yt} ({e2})")
                    fail_yf += 1

        if len(price_buf) >= 500:
            # Dedup PRIMA di scrivere - se lo stesso (ticker,exchange,date)
            # appare due volte nello stesso blocco, l'upsert fallisce con
            # "ON CONFLICT DO UPDATE command cannot affect row a second
            # time" e l'INTERO blocco va perso (26/7/2026, causa reale di
            # APAC ancora fermo nonostante gli altri fix).
            dedup = {}
            for row in price_buf:
                dedup[(row["ticker"], row["exchange"], row["date"])] = row
            price_buf_clean = list(dedup.values())
            rw = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=price_buf_clean)
            if rw.status_code not in (200, 201, 204):
                log(f"  ERRORE SCRITTURA prezzi: HTTP {rw.status_code} - {rw.text[:300]}")
            price_buf = []
        time.sleep(random.uniform(3.0, 7.0))

if price_buf:
    dedup = {}
    for row in price_buf:
        dedup[(row["ticker"], row["exchange"], row["date"])] = row
    price_buf_clean = list(dedup.values())
    rw = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=price_buf_clean)
    if rw.status_code not in (200, 201, 204):
        log(f"  ERRORE SCRITTURA prezzi (finale): HTTP {rw.status_code} - {rw.text[:300]}")
log("  Prezzi Yahoo: ok=" + str(ok_yf) + " fail=" + str(fail_yf))
if saltate_seduta_aperta:
    log("  BLOCCO SICUREZZA: scartate " + str(saltate_seduta_aperta) +
        " barre di sedute non ancora chiuse (esecuzione a mercato aperto). "
        "Verranno riprese alla prossima esecuzione a mercati chiusi.")
ok_prices = ok_yf; fail_prices = fail_yf

# ── 3. LEGGI PREZZI DA prices_eod ────────────────────────────
log("\n[3/5] Lettura prezzi da prices_eod...")
CHUNK = 20
all_ph = defaultdict(list)
chunk_fail_log = []  # DIAGNOSTICA 29/7/2026: quali chunk restano vuoti e perche'
for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        offset_p = 0
        got_any = False
        last_status = None
        last_text = ""
        # Limita a ultimi 400 giorni — sufficiente per momentum 12 mesi
        from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        while True:
            batch = None
            last_text = ""
            for attempt in range(3):
                rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                    params={"select": "ticker,date,adj_close",
                            "exchange": "eq." + exchange,
                            "ticker": "in.(" + ",".join(chunk) + ")",
                            "date": "gte." + from_400d,
                            "order": "ticker,date.desc",
                            "limit": "1000", "offset": str(offset_p)})
                last_status = rp.status_code
                try:
                    batch = rp.json()
                except Exception as e:
                    batch = None
                    last_text = f"JSON decode error: {e} — body: {rp.text[:200]}"
                if isinstance(batch, list):
                    break
                last_text = f"risposta non e' una lista: {str(batch)[:200]}"
                time.sleep(0.5 * (attempt + 1))
            if not isinstance(batch, list):
                # FIX 29/7/2026: prima, se una pagina SUCCESSIVA alla prima
                # falliva (es. errore transitorio/timeout su un chunk con
                # piu' di 1000 righe totali su 400 giorni), il chunk restava
                # "got_any=True" grazie alle pagine precedenti gia' andate a
                # buon fine — la diagnostica per-chunk non vedeva nulla di
                # anomalo, ma i titoli le cui righe cadevano nella pagina
                # persa restavano silenziosamente senza dati recenti (causa
                # reale, sospetta, di WES e altri titoli ASX/TSE/SEHK fermi
                # pur con prices_eod corretto). Ora si ritenta fino a 3
                # volte per pagina prima di arrendersi, e si logga
                # esplicitamente quando una pagina viene persa DOPO che il
                # chunk aveva gia' dati parziali.
                chunk_fail_log.append(
                    f"{exchange} chunk#{i//CHUNK} offset={offset_p} ({chunk[0]}..{chunk[-1]}, {len(chunk)} titoli) "
                    f"HTTP={last_status} {last_text} — persa dopo 3 tentativi"
                    + (" [PARZIALE: chunk aveva gia' dati da pagine precedenti]" if got_any else "")
                )
                break
            if not batch:
                break
            got_any = True
            for d in batch:
                if d["adj_close"] is not None:
                    all_ph[(d["ticker"], exchange)].append(
                        {"date": d["date"], "close": d["adj_close"]})
            offset_p += 1000
            if len(batch) < 1000: break
        if not got_any:
            chunk_fail_log.append(
                f"{exchange} chunk#{i//CHUNK} ({chunk[0]}..{chunk[-1]}, {len(chunk)} titoli) "
                f"totalmente vuoto"
            )
        time.sleep(0.02)
log(f"  Prezzi caricati: {len(all_ph)} titoli")
if chunk_fail_log:
    log(f"  DIAGNOSTICA: {len(chunk_fail_log)} problemi rilevati su {sum(len(v) for v in by_exchange.values())//CHUNK+1} chunk totali:")
    for line in chunk_fail_log[:40]:
        log(f"    {line}")

# ── 4. MOMENTUM ──────────────────────────────────────────────
log("\n[4/5] Calcolo momentum...")
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
                         "change1d": chg1d, "price": last_px,
                         "_last_date": last_date.strftime("%Y-%m-%d")})
    ok += 1

for i in range(0, len(mom_updates), 100):
    clean_batch = [{k: v for k, v in m.items() if k != "_last_date"} for m in mom_updates[i:i+100]]
    requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=clean_batch)
log(f"  Momentum ok={ok} fail={fail}")
ok_momentum = ok

latest_price_updates = []
for m in mom_updates:
    price = m.get("price")
    chg = m.get("change1d")
    prev_price = (price / (1 + chg)) if (price is not None and chg is not None and (1 + chg) != 0) else None
    latest_price_updates.append({
        "ticker": m["ticker"], "exchange": m["exchange"],
        "price": price, "prev_price": prev_price,
        "price_date": m.get("_last_date"), "change1d": chg,
    })
# FIX 29/7/2026: stesso identico bug gia' risolto per prices_eod il
# 26/7/2026 (vedi commento sopra), mai applicato qui - se lo stesso
# (ticker,exchange) appare due volte nello stesso batch di 500, l'upsert
# fallisce con "ON CONFLICT DO UPDATE command cannot affect row a second
# time" e l'INTERO batch va perso, SENZA NESSUN LOG (il risultato della
# POST non veniva nemmeno controllato). Causa reale per cui prices_eod
# risultava sempre aggiornato ma latest_prices (letta dallo screener per
# velocita') restava indietro di giorni per centinaia di titoli, su tutti
# i mercati (ASX, TSE, SEHK...) — non un problema di dati Yahoo, i prezzi
# grezzi erano sempre corretti, solo la cache non si aggiornava.
dedup_lp = {}
for row in latest_price_updates:
    dedup_lp[(row["ticker"], row["exchange"])] = row
latest_price_updates_clean = list(dedup_lp.values())
lp_fail = 0
for i in range(0, len(latest_price_updates_clean), 500):
    rlp = requests.post(SUPABASE_URL + "/rest/v1/latest_prices?on_conflict=ticker,exchange", headers=headers_up, json=latest_price_updates_clean[i:i+500])
    if rlp.status_code not in (200, 201, 204):
        lp_fail += len(latest_price_updates_clean[i:i+500])
        log(f"  ERRORE SCRITTURA latest_prices: HTTP {rlp.status_code} - {rlp.text[:300]}")
log(f"  latest_prices aggiornata: {len(latest_price_updates_clean)} titoli (falliti: {lp_fail})")

# ── 5. RANK APAC ─────────────────────────────────────────────
log("\n[5/5] Ricalcolo rank APAC...")
all_data = []
offset = 0
universe_keys = {(s['ticker'], s['exchange']) for s in all_stocks}
while True:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m,mom1w,mom1m",
                "exchange": "in.(TSE,SEHK,ASX)",
                "offset": str(offset), "limit": "1000"})
    data = r.json()
    if not isinstance(data, list) or not data: break
    all_data.extend([d for d in data if (d["ticker"], d["exchange"]) in universe_keys]); offset += 1000
    if len(data) < 1000: break
log(f"  Fundamentals: {len(all_data)}")

# Mom maps da mom_updates (prezzi appena scaricati) NON dal DB vecchio
mom1w_map  = {(d["ticker"], d["exchange"]): d.get("mom1w")  for d in mom_updates}
mom1m_map  = {(d["ticker"], d["exchange"]): d.get("mom1m")  for d in mom_updates}
mom6m_map  = {(d["ticker"], d["exchange"]): d.get("mom6m")  for d in mom_updates}
mom12m_map = {(d["ticker"], d["exchange"]): d.get("mom12m") for d in mom_updates}

RANK_GROUPS = {"JPN": ["TSE"], "HKG": ["SEHK"], "AUS": ["ASX"]}

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
        log(f"  {country}: {len(res)} rankati")

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
log(f"  Rank APAC: {ok}/{len(rank_updates)}")

# Combined rank AP = TSE+SEHK+ASX
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"] + d["growth_score"] for d in all_scores]
combined_updates = [{"ticker": d["ticker"], "exchange": d["exchange"],
                     "combined_rank": min(99, pct_rank(sum_arr, d["value_score"] + d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
log(f"  Combined rank AP: {ok}/{len(combined_updates)}")
ok_rank = ok

# ── INDICI APAC ───────────────────────────────────────────────
log("\n  Aggiornamento indici APAC...")
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
        if r.status_code != 200: log(f"  ERR {name}: HTTP {r.status_code}"); continue
        data_raw = r.json()
        if not isinstance(data_raw, list) or not data_raw:
            log(f"  ERR {name}: no data"); continue
        data_sorted = sorted(data_raw, key=lambda x: x["date"])
        valid = [d for d in data_sorted if d.get("close") is not None and float(d["close"]) > 0]
        if not valid: log(f"  ERR {name}: nessun close valido"); continue
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
        log(f"  {name}: {last:,.2f} ({change1d:+.2f}%)")
        ok_idx += 1
    except Exception as e: log(f"  ERR {name}: {e}")
    time.sleep(0.2)
log(f"  Indici APAC: {ok_idx}/{len(APAC_INDICES)}")

# ── RIPARAZIONE FINALE latest_prices ─────────────────────────
# FIX 29/7/2026: nonostante i fix precedenti (dedup+log sulla scrittura,
# retry sulla lettura a chunk), in alcune esecuzioni una minoranza di
# titoli restava con latest_prices indietro pur con prices_eod sempre
# corretto (verificato su WES/BHP) — causa sospetta: rate limiting su
# Supabase dopo l'uso intenso di chiamate nei passi precedenti, dato che
# la STESSA identica lettura a chunk, testata isolata, trova sempre tutti
# i titoli. Invece di continuare a inseguire una causa intermittente,
# questo passo finale VERIFICA e RIPARA: confronta la price_date di ogni
# titolo con quella prevalente del suo mercato, e per chi resta indietro
# rilegge SOLO quel titolo (query singola, quindi affidabile anche se il
# batch grande aveva avuto un problema) direttamente da prices_eod e
# riscrive la sua riga in latest_prices.
log("\n[6/6] Verifica e riparazione latest_prices...")
from collections import Counter as _Counter
lp_current = {}
for ex in by_exchange.keys():
    offset_lp = 0
    while True:
        rlpq = requests.get(SUPABASE_URL + "/rest/v1/latest_prices", headers=headers_r,
            params={"select": "ticker,exchange,price_date", "exchange": "eq." + ex,
                     "limit": "1000", "offset": str(offset_lp)})
        try:
            batch_lp = rlpq.json()
        except Exception:
            break
        if not isinstance(batch_lp, list) or not batch_lp: break
        for row in batch_lp:
            lp_current[(row["ticker"], row["exchange"])] = row.get("price_date")
        offset_lp += 1000
        if len(batch_lp) < 1000: break

repaired = repair_fail = 0
for ex, tickers in by_exchange.items():
    dates_here = [lp_current.get((tk, ex)) for tk in tickers if lp_current.get((tk, ex))]
    if not dates_here: continue
    prevalent_date = _Counter(dates_here).most_common(1)[0][0]
    stragglers = [tk for tk in tickers if lp_current.get((tk, ex)) != prevalent_date]
    for tk in stragglers:
        try:
            rpx = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "date,adj_close", "ticker": "eq." + tk, "exchange": "eq." + ex,
                        "order": "date.desc", "limit": "2"})
            rows_px = rpx.json()
            if not isinstance(rows_px, list) or len(rows_px) < 1: continue
            last_row = rows_px[0]
            prev_row = rows_px[1] if len(rows_px) > 1 else None
            chg = round(last_row["adj_close"] / prev_row["adj_close"] - 1, 6) if (prev_row and prev_row.get("adj_close")) else None
            prev_price = (last_row["adj_close"] / (1 + chg)) if (chg is not None and (1 + chg) != 0) else None
            rup = requests.post(SUPABASE_URL + "/rest/v1/latest_prices?on_conflict=ticker,exchange",
                headers=headers_up, json=[{"ticker": tk, "exchange": ex, "price": last_row["adj_close"],
                "prev_price": prev_price, "price_date": last_row["date"], "change1d": chg}])
            if rup.status_code in (200, 201, 204): repaired += 1
            else: repair_fail += 1
        except Exception:
            repair_fail += 1
        time.sleep(0.05)
log(f"  latest_prices riparata: {repaired} titoli corretti, {repair_fail} falliti")
# ── FASE B: TITOLI MAI SCRITTI in latest_prices ──────────────
# FIX 29/7/2026 (Kimi + Claude): la Fase A sopra confronta la price_date
# di un record ESISTENTE — se il titolo non ha MAI avuto una riga in
# latest_prices, la Fase A non lo vede affatto (invisibile al repair).
# Trovato cosi': US aveva 642 titoli mai scritti (es. Ford, GoDaddy,
# Fiserv) pur con dati perfettamente corretti in prices_eod. Questa fase
# trova chi e' in_universe ma assente del tutto da latest_prices, e lo
# scrive leggendo da prices_eod.
log("\n[Riparazione B] Titoli mai scritti in latest_prices...")
missing_filled = missing_notfound = 0
for ex, tickers in by_exchange.items():
    have_here = set(tk for (tk, exx) in lp_current.keys() if exx == ex)
    missing_here = [tk for tk in tickers if tk not in have_here]
    batch_missing = []
    for tk in missing_here:
        try:
            rpx = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                params={"select": "date,adj_close", "ticker": "eq." + tk, "exchange": "eq." + ex,
                        "order": "date.desc", "limit": "2"})
            rows_px = rpx.json()
            if not isinstance(rows_px, list) or len(rows_px) < 1:
                missing_notfound += 1
                continue
            last_row = rows_px[0]
            prev_row = rows_px[1] if len(rows_px) > 1 else None
            chg = round(last_row["adj_close"] / prev_row["adj_close"] - 1, 6) if (prev_row and prev_row.get("adj_close")) else None
            prev_price = (last_row["adj_close"] / (1 + chg)) if (chg is not None and (1 + chg) != 0) else None
            batch_missing.append({"ticker": tk, "exchange": ex, "price": last_row["adj_close"],
                "prev_price": prev_price, "price_date": last_row["date"], "change1d": chg})
        except Exception:
            missing_notfound += 1
        time.sleep(0.03)
    for i in range(0, len(batch_missing), 500):
        rup2 = requests.post(SUPABASE_URL + "/rest/v1/latest_prices?on_conflict=ticker,exchange",
            headers=headers_up, json=batch_missing[i:i+500])
        if rup2.status_code in (200, 201, 204):
            missing_filled += len(batch_missing[i:i+500])
log(f"  Titoli mai scritti riempiti: {missing_filled}, non trovati nemmeno in prices_eod: {missing_notfound}")


end_time = time_module.time()

# ── QUINTILI DI SETTORE PRECALCOLATI ─────────────────────────
# FIX 30/7/2026 (Kimi + Claude): il calcolo dei quintili di settore/
# continente per la pagina Sectors girava ad ogni richiesta dell'API
# scorrendo TUTTE le righe restituite (fino a ~7.889 per Global) — causa
# principale dei 25s di caricamento. Qui si calcolano UNA VOLTA AL GIORNO
# le somme parziali per (exchange, settore): sum(rank*mkt_cap) e
# sum(mkt_cap) per EPS growth e Revenue growth. Sono sommabili: l'API puo'
# ricostruire il quintile per QUALSIASI combinazione di mercati (Global,
# EU, un singolo paese) sommando solo le righe pertinenti di questa
# tabella (poche decine), invece di ricalcolare da zero su migliaia di
# titoli grezzi.
log("\n[Quintili] Calcolo somme parziali per settore...")
sector_by_key = {}
offset_s = 0
while True:
    rs_q = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,sector", "exchange": "in.(" + ",".join(by_exchange.keys()) + ")",
                "in_universe": "eq.true", "limit": "1000", "offset": str(offset_s)})
    batch_s = rs_q.json()
    if not isinstance(batch_s, list) or not batch_s: break
    for row in batch_s:
        sector_by_key[(row["ticker"], row["exchange"])] = row.get("sector") or "Unknown"
    offset_s += 1000
    if len(batch_s) < 1000: break

partials = {}  # (exchange, sector) -> {sum_eps_w, sum_eps_wt, sum_rev_w, sum_rev_wt, n}
offset_f = 0
while True:
    rf_q = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,mkt_cap,rank_eps_gr,rank_rev_gr",
                "exchange": "in.(" + ",".join(by_exchange.keys()) + ")",
                "limit": "1000", "offset": str(offset_f)})
    batch_f = rf_q.json()
    if not isinstance(batch_f, list) or not batch_f: break
    for row in batch_f:
        key = (row["ticker"], row["exchange"])
        sector = sector_by_key.get(key)
        if not sector: continue
        pkey = (row["exchange"], sector)
        if pkey not in partials:
            partials[pkey] = {"sum_eps_w": 0.0, "sum_eps_wt": 0.0, "sum_rev_w": 0.0, "sum_rev_wt": 0.0, "n": 0}
        p = partials[pkey]
        mc = row.get("mkt_cap")
        if mc:
            if row.get("rank_eps_gr") is not None:
                p["sum_eps_w"] += row["rank_eps_gr"] * mc
                p["sum_eps_wt"] += mc
            if row.get("rank_rev_gr") is not None:
                p["sum_rev_w"] += row["rank_rev_gr"] * mc
                p["sum_rev_wt"] += mc
        p["n"] += 1
    offset_f += 1000
    if len(batch_f) < 1000: break

partial_rows = [{"exchange": ex, "sector": sec, "sum_eps_weighted": v["sum_eps_w"],
    "sum_eps_weight": v["sum_eps_wt"], "sum_rev_weighted": v["sum_rev_w"],
    "sum_rev_weight": v["sum_rev_wt"], "n_stocks": v["n"],
    # FIX 2/8/2026: updated_at va scritto ESPLICITAMENTE. Il valore di
    # default della colonna scatta solo alla CREAZIONE della riga, non
    # sugli aggiornamenti successivi: le righe create il 30/7 mostravano
    # ancora quella data pur essendo i valori riscritti ogni notte, e il
    # rapporto giornaliero segnalava (a torto) i quintili come fermi.
    "updated_at": datetime.utcnow().isoformat()} for (ex, sec), v in partials.items()]
q_ok = 0
for i in range(0, len(partial_rows), 500):
    rq = requests.post(SUPABASE_URL + "/rest/v1/sector_quintile_partials?on_conflict=exchange,sector",
        headers=headers_up, json=partial_rows[i:i+500])
    if rq.status_code in (200, 201, 204):
        q_ok += len(partial_rows[i:i+500])
    else:
        log(f"  ERRORE SCRITTURA sector_quintile_partials: HTTP {rq.status_code} - {rq.text[:200]}")
log(f"  Quintili di settore: {q_ok} righe (exchange,settore) aggiornate")


# ── AGGIORNA LA VISTA DEI PREZZI CORRENTI ────────────────────
# FIX 5/8/2026 — FONTE UNICA: la tabella latest_prices e' stata
# sostituita dalla vista materializzata latest_prices_mv, calcolata su
# prices_eod. Non va piu' scritta: va solo ricalcolata. Cosi' lo screener
# e il grafico mostrano per forza lo stesso numero, perche' leggono la
# stessa fonte. Prima erano due scritture separate e bastava che una
# restasse indietro per far divergere i due valori nella stessa pagina.
# ── VERIFICA SEDUTA: recupera cio' che il download di gruppo ha perso ──
# FIX 5/8/2026. Problema osservato piu' volte e mai spiegato: il download
# in blocco riesce (ok=2625, fail=1) ma NON contiene l'ultima seduta
# chiusa, mentre lo stesso titolo interrogato singolarmente ce l'ha.
# Risultato: l'Europa restava indietro di una seduta e nessuno se ne
# accorgeva, perche' lo script dichiarava di aver scaricato tutto.
# Casi reali: 4/8 ore 12:19 (nessun titolo col 3/8, disponibile da 21 ore)
# e 5/8 ore 00:30 (71 titoli su 2136 col 4/8).
# Questa fase non prova a spiegare il perche': verifica il risultato e
# ripara. Stabilisce qual e' la vera ultima seduta del mercato (con
# download SINGOLI, affidabili), controlla chi non ce l'ha e lo riscarica
# a blocchi piccoli. Funziona quindi anche per cause che non conosciamo.
log("\n[2b/5] Verifica ultima seduta per mercato...")
ymap_v = {}
for _s in all_stocks:
    ymap_v[(_s["ticker"], _s["exchange"])] = _s.get("yahoo_ticker") or yahoo_ticker(_s["ticker"], _s["exchange"])

def _ultima_seduta_reale(exchange, tickers):
    """Ultima seduta CHIUSA realmente pubblicata da Yahoo per il mercato.
    Interroga singolarmente alcuni titoli: il download singolo non ha mai
    mostrato il problema del blocco."""
    migliore = None
    for tk in tickers[:5]:
        yt = ymap_v.get((tk, exchange))
        if not yt:
            continue
        try:
            d1 = yf.download(yt, period="12d", interval="1d",
                             auto_adjust=True, progress=False)
            if d1.empty:
                continue
            cl1 = d1["Close"]
            if isinstance(cl1, pd.DataFrame):
                cl1 = cl1.iloc[:, 0]
            cl1 = cl1.dropna()
            for i in range(len(cl1) - 1, -1, -1):
                ds1 = cl1.index[i].strftime("%Y-%m-%d")
                if seduta_conclusa(ds1):
                    if migliore is None or ds1 > migliore:
                        migliore = ds1
                    break
        except Exception:
            pass
        time.sleep(0.4)
    return migliore

recuperati_tot = 0
for _ex, _tickers in by_exchange.items():
    _seduta = _ultima_seduta_reale(_ex, _tickers)
    if not _seduta:
        log(f"  {_ex}: impossibile stabilire l'ultima seduta, salto")
        continue
    _presenti = set()
    _off = 0
    while True:
        _rr = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "ticker", "exchange": "eq." + _ex,
                    "date": "eq." + _seduta, "limit": "1000", "offset": str(_off)})
        try:
            _b = _rr.json()
        except Exception:
            break
        if not isinstance(_b, list) or not _b:
            break
        _presenti.update(x["ticker"] for x in _b)
        _off += 1000
        if len(_b) < 1000:
            break
    _mancanti = [t for t in _tickers if t not in _presenti]
    if not _mancanti:
        log(f"  {_ex}: seduta {_seduta} completa ({len(_tickers)} titoli)")
        continue
    log(f"  {_ex}: seduta {_seduta} — {len(_mancanti)}/{len(_tickers)} senza questa seduta, verifico su Yahoo")
    _buf = []
    _da = (datetime.strptime(_seduta, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
    _a = (datetime.strptime(_seduta, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    for _j in range(0, len(_mancanti), 40):
        _sub = [t for t in _mancanti[_j:_j+40] if ymap_v.get((t, _ex))]
        if not _sub:
            continue
        _yts = [ymap_v[(t, _ex)] for t in _sub]
        _rev = {ymap_v[(t, _ex)]: t for t in _sub}
        try:
            _d2 = yf.download(tickers=" ".join(_yts), start=_da, end=_a, interval="1d",
                              auto_adjust=True, progress=False, threads=True)
            if _d2.empty:
                continue
            if isinstance(_d2.columns, pd.MultiIndex):
                _cl2 = _d2["Close"]
            else:
                _cl2 = _d2[["Close"]].rename(columns={"Close": _yts[0]})
            for _yt in _yts:
                if _yt not in _cl2.columns:
                    continue
                _ser = _cl2[_yt].dropna()
                for _idx, _pr in _ser.items():
                    _ds = _idx.strftime("%Y-%m-%d")
                    if _ds != _seduta or not seduta_conclusa(_ds):
                        continue
                    try:
                        _v = float(_pr)
                    except Exception:
                        continue
                    if _v <= 0:
                        continue
                    _buf.append({"ticker": _rev[_yt], "exchange": _ex,
                                 "date": _ds, "adj_close": round(_v, 6)})
        except Exception as _e:
            log(f"    blocco di recupero fallito: {str(_e)[:80]}")
        time.sleep(1.5)
    _ded = {}
    for _row in _buf:
        _ded[(_row["ticker"], _row["exchange"], _row["date"])] = _row
    _buf = list(_ded.values())
    _scritte = 0
    for _j in range(0, len(_buf), 500):
        _rw = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date",
                            headers=headers_up, json=_buf[_j:_j+500])
        if _rw.status_code in (200, 201, 204):
            _scritte += len(_buf[_j:_j+500])
        else:
            log(f"    ERRORE scrittura recupero: HTTP {_rw.status_code} - {_rw.text[:150]}")
    recuperati_tot += _scritte
    if _scritte:
        log(f"    recuperati {_scritte} titoli")
    else:
        log(f"    nessun recupero: Yahoo non ha la seduta {_seduta} per questi titoli "
            f"(poco scambiati o non ancora pubblicati) — nessuna azione necessaria")
log(f"  Verifica seduta: {recuperati_tot} prezzi recuperati")

log("\n[Vista prezzi] Aggiornamento latest_prices_mv...")
try:
    rmv = requests.post(SUPABASE_URL + "/rest/v1/rpc/refresh_latest_prices",
                        headers={**headers_r, "Content-Type": "application/json"},
                        json={}, timeout=300)
    if rmv.status_code in (200, 204):
        log("  vista aggiornata")
    else:
        log(f"  ERRORE aggiornamento vista: HTTP {rmv.status_code} - {rmv.text[:200]}")
except Exception as e:
    log(f"  ERRORE aggiornamento vista: {e}")

log_entry = {"run_date": TODAY, "market": "APAC", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
log(f"\nLog: leeway={ok_prices} fail={fail_prices} momentum={ok_momentum} rank={ok_rank} durata={int(end_time-start_time)}s")
log("\n" + "=" * 60)
log("DAILY APAC LOAD COMPLETATO")
log("=" * 60)
