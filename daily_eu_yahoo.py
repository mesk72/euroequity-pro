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
import pandas as pd

# ── LOCK ANTI-DOPPIA-ESECUZIONE ──────────────────────────────
# FIX 29/7/2026: stesso lock gia' aggiunto a daily_apac_yahoo.py.
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
ORA_LIMITE_UTC = 17  # Europa: chiusure 17:30 CEST (15:30 UTC) / 17:30 CET (16:30 UTC)
saltate_seduta_aperta = 0

def seduta_conclusa(date_str):
    """True se la seduta di quella data e' sicuramente gia' chiusa."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return False
    return datetime.utcnow() >= d.replace(hour=ORA_LIMITE_UTC, minute=0, second=0)


# BLOCCO GIORNALIERO RIMOSSO 11/8/2026.
# Era stato messo il 30/7 per evitare esecuzioni ripetute nello stesso
# giorno. Ma nel frattempo la strategia e' cambiata: servono PIU' passate
# al giorno, perche' Yahoo pubblica i titoli minori diverse ore dopo la
# chiusura e una sola passata non li prende mai.
# Effetto reale del blocco, misurato l'11/8: l'Asia era girata TRE volte
# il giorno prima (18:00, 19:30, 23:36) e tutte e tre risultavano
# "riuscite", ma solo la prima aveva fatto qualcosa - le altre due erano
# uscite subito. Risultato: Giappone, Hong Kong e Singapore fermi alla
# seduta del 7 agosto con Yahoo che aveva gia' quella del 10.
# Le sovrapposizioni parallele restano impedite da 'concurrency' nel
# workflow, che e' il meccanismo giusto per quello scopo.

_log_buffer = []
def log(msg):
    print(msg)
    _log_buffer.append(str(msg))
    try:
        requests.post(SUPABASE_URL + "/rest/v1/script_logs", headers=headers_up,
            json={"script_name": "daily_eu_yahoo", "log_text": "\n".join(_log_buffer)},
            timeout=10)
    except Exception:
        pass

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
log("=" * 60)
log("FORWARDALPHA DAILY EU LOAD — " + TODAY)
log("=" * 60)

# ── 1. CARICA UNIVERSO EU ────────────────────────────────────
log("\n[1/5] Caricamento universo EU...")
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
log("  Universo EU: " + str(len(all_stocks)) + " titoli")

by_exchange = defaultdict(list)
for s in all_stocks:
    by_exchange[s["exchange"]].append(s["ticker"])

# ── 2. SCARICA PREZZI EOD DA YAHOO FINANCE ──────────────────
log("\n[2/5] Download prezzi EOD da Yahoo Finance...")

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
                end=END_FOR_DOWNLOAD,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if data_yf.empty:
                fail_yf += len(ytickers)
                continue

            # Estrazione robusta (fix Kimi, gia' applicato a US) — un solo
            # ticker con formato anomalo poteva far perdere l'intero chunk.
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
                if yt not in closes.columns:
                    fail_yf += 1
                    continue
                tk, ex = ticker_map[yt]
                last = last_dates.get((tk, ex), "2020-01-01")
                series = closes[yt].dropna()
                for date_idx, price in series.items():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    if date_str <= last: continue
                    if not seduta_conclusa(date_str):
                        saltate_seduta_aperta += 1
                        continue
                    price_buf.append({"ticker": tk, "exchange": ex,
                                      "date": date_str, "adj_close": round(float(price), 6)})
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
            dedup = {}
            for row in price_buf:
                dedup[(row["ticker"], row["exchange"], row["date"])] = row
            price_buf_clean = list(dedup.values())
            rw = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=price_buf_clean)
            if rw.status_code not in (200, 201, 204):
                log(f"  ERRORE SCRITTURA prezzi: HTTP {rw.status_code} - {rw.text[:300]}")
            price_buf = []

        # Pausa random tra chunk
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


# ── COMPLETAMENTO SEDUTA ─────────────────────────────────────
# REGOLA (imposta da Andrea, 7/8/2026): non si accetta nessun titolo
# indietro. Non esiste una soglia "abbastanza aggiornato": 998 su 1000 e'
# un fallimento come 500 su 1000. Per ogni singolo titolo si arriva a una
# di queste due conclusioni, e a nessun'altra:
#   - il prezzo c'e' su Yahoo   -> viene scaricato, costi quel che costi
#   - il prezzo NON c'e'        -> verificato UNO PER UNO con richiesta
#                                  singola, e registrato con il motivo
#
# Perche' la versione precedente non bastava: si fermava quando una
# passata non produceva progressi. Ma i titoli che restano indietro sono
# proprio quelli che il download di gruppo perde sistematicamente (poco
# scambiati, o penalizzati dai limiti di frequenza di Yahoo): rinunciare
# quando il gruppo non li restituisce piu' significa non prenderli mai.
# Ora, quando il gruppo smette di dare risultati, si passa alle richieste
# SINGOLE, che sono lente ma affidabili.
log("\n[Completamento seduta] Nessun titolo indietro: verifico uno per uno...")

_ymap = {}
for _s in all_stocks:
    _ymap[(_s["ticker"], _s["exchange"])] = _s.get("yahoo_ticker") or yahoo_ticker(_s["ticker"], _s["exchange"])


def _seduta_attesa(_ex, _tickers):
    """Ultima seduta CHIUSA che Yahoo ha per questo mercato.
    FIX 7/8/2026: si usa il valore PREVALENTE fra i titoli di riferimento,
    non il massimo. Col massimo bastava un solo titolo in anticipo per far
    risultare "mancanti" tutti gli altri: il 7/8 su Zurigo un unico titolo
    aveva il 6 agosto mentre il resto del mercato si fermava al 5, e lo
    script ha cercato inutilmente 137 titoli che Yahoo non aveva ancora
    pubblicato. Si campionano piu' titoli (12 invece di 6) presi anche
    dal centro dell'elenco, non solo dai primi in ordine alfabetico."""
    _voti = []
    _campione = _tickers[:6] + _tickers[len(_tickers) // 2: len(_tickers) // 2 + 6]
    for _tk in _campione:
        _yt = _ymap.get((_tk, _ex))
        if not _yt:
            continue
        try:
            _d = yf.download(_yt, period="12d", interval="1d", auto_adjust=True, progress=False)
            if _d.empty:
                continue
            _c = _d["Close"]
            if isinstance(_c, pd.DataFrame):
                _c = _c.iloc[:, 0]
            _c = _c.dropna()
            for _i in range(len(_c) - 1, -1, -1):
                _ds = _c.index[_i].strftime("%Y-%m-%d")
                if seduta_conclusa(_ds):
                    _voti.append(_ds)
                    break
        except Exception:
            pass
        time.sleep(0.3)
    if not _voti:
        return None
    _conta = {}
    for _v in _voti:
        _conta[_v] = _conta.get(_v, 0) + 1
    # il piu' votato; a parita' di voti si preferisce la data piu' recente
    return sorted(_conta.items(), key=lambda x: (x[1], x[0]), reverse=True)[0][0]


def _chi_manca(_ex, _tickers, _seduta):
    _pres = set()
    _off = 0
    while True:
        try:
            _r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                              params={"select": "ticker", "exchange": "eq." + _ex,
                                      "date": "eq." + _seduta,
                                      "limit": "1000", "offset": str(_off)}, timeout=60)
            _b = _r.json()
        except Exception:
            break
        if not isinstance(_b, list) or not _b:
            break
        _pres.update(_x["ticker"] for _x in _b)
        _off += 1000
        if len(_b) < 1000:
            break
    return [_t for _t in _tickers if _t not in _pres]


def _scrivi(_righe):
    _ok = 0
    for _i in range(0, len(_righe), 500):
        _w = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date",
                           headers=headers_up, json=_righe[_i:_i + 500])
        if _w.status_code in (200, 201, 204):
            _ok += len(_righe[_i:_i + 500])
    return _ok


def _gruppo(_ex, _mancanti, _seduta):
    """Tentativo a blocchi di 40: veloce, recupera la maggior parte."""
    _dopo = (datetime.strptime(_seduta, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    _prima = (datetime.strptime(_seduta, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    _buf = []
    for _i in range(0, len(_mancanti), 40):
        _map = {}
        for _t in _mancanti[_i:_i + 40]:
            _yt = _ymap.get((_t, _ex))
            if _yt:
                _map[_yt] = _t
        if not _map:
            continue
        try:
            _df = yf.download(tickers=" ".join(_map.keys()), start=_prima, end=_dopo,
                              interval="1d", auto_adjust=True, progress=False, threads=True)
            if _df.empty:
                continue
            _cl = _df["Close"] if isinstance(_df.columns, pd.MultiIndex) \
                else _df[["Close"]].rename(columns={"Close": list(_map.keys())[0]})
            for _yt, _t in _map.items():
                if _yt not in _cl.columns:
                    continue
                for _idx, _pr in _cl[_yt].dropna().items():
                    if _idx.strftime("%Y-%m-%d") == _seduta and seduta_conclusa(_seduta):
                        _buf.append({"ticker": _t, "exchange": _ex, "date": _seduta,
                                     "adj_close": round(float(_pr), 6)})
        except Exception:
            pass
        time.sleep(1.2)
    _ded = {}
    for _r in _buf:
        _ded[(_r["ticker"], _r["exchange"], _r["date"])] = _r
    return _scrivi(list(_ded.values()))


def _singoli(_ex, _mancanti, _seduta):
    """Ultima istanza: una richiesta per ciascun titolo. Lento ma e' il
    metodo che da' la risposta definitiva. Restituisce (scritti, assenti),
    dove 'assenti' sono i titoli per cui Yahoo NON ha quella seduta -
    verificato singolarmente, non per esclusione."""
    _buf = []
    _assenti = []
    for _t in _mancanti:
        _yt = _ymap.get((_t, _ex))
        if not _yt:
            _assenti.append((_t, "nessun codice Yahoo"))
            continue
        try:
            _d = yf.download(_yt, period="10d", interval="1d", auto_adjust=True, progress=False)
            if _d.empty:
                _assenti.append((_t, "Yahoo non ha dati"))
            else:
                _c = _d["Close"]
                if isinstance(_c, pd.DataFrame):
                    _c = _c.iloc[:, 0]
                _c = _c.dropna()
                _map = {_i.strftime("%Y-%m-%d"): float(_v) for _i, _v in _c.items()}
                if _seduta in _map:
                    _buf.append({"ticker": _t, "exchange": _ex, "date": _seduta,
                                 "adj_close": round(_map[_seduta], 6)})
                else:
                    _ultimo = max(_map) if _map else "nessuna"
                    _assenti.append((_t, "ultima seduta su Yahoo: " + _ultimo))
        except Exception as _e:
            _assenti.append((_t, "errore: " + str(_e)[:40]))
        time.sleep(0.35)
    return _scrivi(_buf), _assenti


_sedute = {}
for _ex, _tk in by_exchange.items():
    _sedute[_ex] = _seduta_attesa(_ex, _tk)

_non_disponibili = []
recuperati_tot = 0

for _ex, _tickers in by_exchange.items():
    _seduta = _sedute.get(_ex)
    if not _seduta:
        log(f"  {_ex}: impossibile stabilire l'ultima seduta, salto")
        continue

    # fase A: tentativi a gruppi, finche' producono risultati
    for _p in range(1, 4):
        _manc = _chi_manca(_ex, _tickers, _seduta)
        if not _manc:
            break
        _r = _gruppo(_ex, _manc, _seduta)
        recuperati_tot += _r
        if _r == 0:
            break

    # fase B: chi resta viene interrogato UNO PER UNO. Nessuna rinuncia
    # prima di questo passaggio: e' l'unico modo per distinguere davvero
    # "Yahoo non ce l'ha" da "il download di gruppo l'ha perso".
    _manc = _chi_manca(_ex, _tickers, _seduta)
    if _manc:
        _r, _assenti = _singoli(_ex, _manc, _seduta)
        recuperati_tot += _r
        for _t, _mot in _assenti:
            _non_disponibili.append((_ex, _t, _mot))
        log(f"  {_ex}: seduta {_seduta} — {len(_manc)} da verificare singolarmente, "
            f"{_r} recuperati, {len(_assenti)} non disponibili su Yahoo")
    else:
        log(f"  {_ex}: seduta {_seduta} — completo")

# riepilogo: quanti titoli hanno DAVVERO l'ultima seduta
_completi = 0
_totali = 0
for _ex, _tickers in by_exchange.items():
    _totali += len(_tickers)
    _seduta = _sedute.get(_ex)
    if _seduta:
        _completi += len(_tickers) - len(_chi_manca(_ex, _tickers, _seduta))

log(f"  RISULTATO: {_completi}/{_totali} titoli hanno l'ultima seduta "
    f"({recuperati_tot} recuperati adesso)")
if _non_disponibili:
    log(f"  {len(_non_disponibili)} titoli NON disponibili su Yahoo (verificati uno per uno):")
    for _ex, _t, _mot in _non_disponibili[:40]:
        log(f"    {_t}.{_ex} — {_mot}")
    if len(_non_disponibili) > 40:
        log(f"    ...e altri {len(_non_disponibili) - 40}")
if _completi + len(_non_disponibili) < _totali:
    log(f"  ATTENZIONE: {_totali - _completi - len(_non_disponibili)} titoli non "
        f"aggiornati e non giustificati. Da controllare.")

# ── 3. LEGGI PREZZI DA prices_eod ────────────────────────────
log("\n[3/5] Lettura prezzi da prices_eod...")
CHUNK = 20
all_ph = defaultdict(list)
for exchange, tickers in by_exchange.items():
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i+CHUNK]
        offset_p = 0
        # Limita a ultimi 400 giorni — sufficiente per momentum 12 mesi
        from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        while True:
            # FIX 29/7/2026: stesso fix applicato ad APAC — nessun timeout
            # ne' retry poteva troncare silenziosamente la lettura sotto
            # carico prolungato (centinaia di richieste sequenziali).
            rp = None
            for attempt in range(3):
                try:
                    rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
                        params={"select": "ticker,date,adj_close",
                                "exchange": "eq." + exchange,
                                "ticker": "in.(" + ",".join(chunk) + ")",
                                "date": "gte." + from_400d,
                                "order": "ticker,date.desc",
                                "limit": "1000", "offset": str(offset_p)},
                        timeout=20)
                    break
                except Exception:
                    time.sleep(1.0 + attempt)
            if rp is None: break
            try:
                batch = rp.json()
            except Exception:
                break
            if not isinstance(batch, list) or not batch: break
            for d in batch:
                if d["adj_close"] is not None:
                    all_ph[(d["ticker"], exchange)].append(
                        {"date": d["date"], "close": d["adj_close"]})
            offset_p += 1000
            if len(batch) < 1000: break
        time.sleep(0.02)
log("  Prezzi caricati: " + str(len(all_ph)) + " titoli")

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
log("  Momentum ok=" + str(ok) + " fail=" + str(fail))
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
# FIX 29/7/2026: stesso bug gia' risolto per prices_eod il 26/7 (duplicati
# nello stesso batch fanno fallire l'INTERO batch di 500, in silenzio -
# causa reale scoperta su APAC di latest_prices indietro di giorni pur
# con prices_eod sempre corretto), applicato qui preventivamente.
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
log("  latest_prices aggiornata: " + str(len(latest_price_updates_clean)) + " titoli (falliti: " + str(lp_fail) + ")")

# ── 5. FX ────────────────────────────────────────────────────
log("\n  Aggiornamento FX...")
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
log("  FX salvati")

# ── 6. RANK EU ───────────────────────────────────────────────
log("\n[5/5] Ricalcolo rank EU...")
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
log("  Fundamentals: " + str(len(all_data)))

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
        log("  " + country + ": " + str(len(res)) + " rankati")

ranked_exchanges = set(ex for exs in RANK_GROUPS.values() for ex in exs)
unranked = [d for d in all_data if d["exchange"] not in ranked_exchanges and d["exchange"] not in NO_RANK]
if unranked:
    rank_updates.extend(calc_ranks(unranked))

ok = 0
for i in range(0, len(rank_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=rank_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(rank_updates[i:i+100])
log("  Rank EU: " + str(ok) + "/" + str(len(rank_updates)))

# Combined rank EU
all_scores = [d for d in rank_updates if d.get("value_score") is not None and d.get("growth_score") is not None]
sum_arr    = [d["value_score"] + d["growth_score"] for d in all_scores]
combined_updates = [{"ticker": d["ticker"], "exchange": d["exchange"],
                     "combined_rank": min(99, pct_rank(sum_arr, d["value_score"] + d["growth_score"]))}
                    for d in all_scores]
ok = 0
for i in range(0, len(combined_updates), 100):
    r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=combined_updates[i:i+100])
    if r.status_code in (200, 201, 204): ok += len(combined_updates[i:i+100])
log("  Combined rank EU: " + str(ok) + "/" + str(len(combined_updates)))
ok_rank = ok

# ── INDICI EU ────────────────────────────────────────────────
log("\n  Aggiornamento indici EU...")
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
        if r.status_code != 200: log("  ERR " + name + ": HTTP " + str(r.status_code)); continue
        data_raw = r.json()
        if not isinstance(data_raw, list) or not data_raw:
            log("  ERR " + name + ": no data"); continue
        data_sorted = sorted(data_raw, key=lambda x: x["date"])
        valid = [d for d in data_sorted if d.get("close") is not None and float(d["close"]) > 0]
        if not valid: log("  ERR " + name + ": nessun close valido"); continue
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
        log("  " + name + ": " + str(round(last, 2)) + " (" + str(change1d) + "%)")
        ok_idx += 1
    except Exception as e: log("  ERR " + name + ": " + str(e))
    time.sleep(0.2)
log("  Indici EU: " + str(ok_idx) + "/" + str(len(EU_INDICES)))

# ── RIPARAZIONE FINALE latest_prices ─────────────────────────
# FIX 29/7/2026: stesso repair pass gia' aggiunto a daily_apac_yahoo.py -
# confronta la price_date di ogni titolo con quella prevalente del suo
# mercato, e per chi resta indietro rilegge SOLO quel titolo da
# prices_eod (query singola, affidabile anche se il batch grande aveva
# avuto un problema) e riscrive la sua riga in latest_prices.
log("\n[Riparazione] Verifica e riparazione latest_prices...")
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
log("  latest_prices riparata: " + str(repaired) + " titoli corretti, " + str(repair_fail) + " falliti")
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


# ── VISTA DEI PREZZI CORRENTI ────────────────────────────────
# FIX 6/8/2026: la chiamata HTTP a refresh_latest_prices() e' stata
# rimossa perche' andava SEMPRE in timeout (errore 57014): Supabase
# chiude le richieste HTTP dopo circa un minuto e il ricalcolo non ci
# stava dentro. Risultato: la vista restava ferma e il sito mostrava
# prezzi vecchi mentre il database aveva quelli nuovi.
# Ora la vista viene ricalcolata dal database stesso ogni 10 minuti
# tramite pg_cron (lavoro 'aggiorna-prezzi-correnti'), senza passare da
# HTTP e quindi senza limite di tempo. Gli script non devono fare nulla.

log_entry = {"run_date": TODAY, "market": "EU", "prices_updated": ok_prices,
             "prices_failed": fail_prices, "last_price_date": TODAY,
             "momentum_updated": ok_momentum, "rank_updated": ok_rank,
             "duration_seconds": int(end_time - start_time)}
requests.post(SUPABASE_URL + "/rest/v1/daily_log", headers=headers_up, json=[log_entry])
log("\nLog: leeway=" + str(ok_prices) + " fail=" + str(fail_prices) + " momentum=" + str(ok_momentum) + " rank=" + str(ok_rank) + " durata=" + str(int(end_time-start_time)) + "s")
log("\n" + "=" * 60)
log("DAILY EU LOAD COMPLETATO")
log("=" * 60)
