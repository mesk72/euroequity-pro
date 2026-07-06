import os, time, requests
from datetime import datetime, timedelta

# ============================================================
# REBUILD PREZZI 5 ANNI DA LEEWAY — SCRIPT ONE-OFF
# Da usare solo per ricostruire lo storico dopo la contaminazione
# Yahoo/Leeway. Cancella e riscarica tutto lo storico a 5 anni
# per l'universo (in_universe=true) della regione scelta.
# Regione impostata dalla variabile d'ambiente REGION: EU | US | APAC
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
REGION       = os.environ.get("REGION", "").strip().upper()

TODAY    = datetime.now().strftime("%Y-%m-%d")
FROM_5Y  = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

REGIONS = {
    "EU":   ["MIL", "LSE", "XETRA", "PA", "OM", "SWX", "AS", "MC", "BR",
             "HE", "CPSE", "OB", "GR", "VI", "IR", "LS"],
    "US":   ["US", "TSX"],
    "APAC": ["TSE", "SEHK", "ASX", "KRX", "SGX"],
}

if REGION not in REGIONS:
    raise SystemExit(f"REGION non valida: '{REGION}'. Usa uno tra: {list(REGIONS.keys())}")

EXCHANGES = REGIONS[REGION]

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}

LEEWAY_SUFFIX = {
    "MIL":  ".MI",    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":   ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":   ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":   ".IR",    "AT":    ".VI",     "GR":   ".AT",
    "LSE":  ".LSE",   "AIM":   ".AIM",   "SWX":  ".SW",
    "OM":   ".ST",    "NGM":   ".ST",    "OB":   ".OL",
    "CPSE": ".CO",
    "US":   ".US",    "TSX":   ".TO",
    "TSE":  ".TSE",   "ASX":   ".AU",
}

def leeway_ticker(ticker, exchange, primary_ex=""):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "KRX":
        # KOSPI = .KO, KOSDAQ = .KQ (verificato 06/07/2026)
        return ticker.lstrip("A") + (".KQ" if primary_ex == "KOSDAQ" else ".KO")
    if exchange == "SGX":  return ticker + ".SG"
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX":  return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":   return ticker.replace(".", "") + ".BR"
    ticker_clean = ticker.rstrip(".")
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")

def safe_get(url, **kwargs):
    for attempt in range(3):
        try:
            return requests.get(url, timeout=kwargs.pop("timeout", 20), **kwargs)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"    WARN GET fallita dopo 3 tentativi: {e}")
            return None

def safe_delete(url, **kwargs):
    for attempt in range(3):
        try:
            return requests.delete(url, timeout=kwargs.pop("timeout", 20), **kwargs)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"    WARN DELETE fallita dopo 3 tentativi: {e}")
            return None

def safe_post(url, json_data, **kwargs):
    for attempt in range(3):
        try:
            return requests.post(url, json=json_data, timeout=kwargs.pop("timeout", 30), **kwargs)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"    WARN POST fallita dopo 3 tentativi: {e}")
            return None

print("=" * 60)
print(f"REBUILD 5 ANNI PREZZI — REGIONE {REGION} — {TODAY}")
print(f"Da {FROM_5Y} a {TODAY}")
print("=" * 60)

# ── 1. CARICA UNIVERSO ───────────────────────────────────────
print(f"\n[1/2] Caricamento universo {REGION}...")
all_stocks = []
for exchange in EXCHANGES:
    offset = 0
    while True:
        r = safe_get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange,primary_exchange", "in_universe": "eq.true",
                    "exchange": f"eq.{exchange}", "offset": str(offset), "limit": "1000"})
        if r is None: break
        try:
            data = r.json()
        except Exception:
            break
        if not isinstance(data, list) or not data: break
        all_stocks.extend(data)
        offset += 1000
        if len(data) < 1000: break
print(f"  Universo {REGION}: {len(all_stocks)} titoli")
by_exchange = {}
for s in all_stocks:
    by_exchange.setdefault(s["exchange"], 0)
    by_exchange[s["exchange"]] += 1
for ex, n in by_exchange.items():
    print(f"    {ex}: {n}")

# Salta i titoli che hanno gia' storico sufficiente in prices_eod (per
# non rifare da zero un rebuild completo quando serve solo colmare le
# lacune dei titoli appena entrati in universo)
print(f"\n  Verifico quali titoli hanno gia' storico...")
existing_tickers = set()
offset = 0
while True:
    r = safe_get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "ticker,exchange", "exchange": f"in.({','.join(EXCHANGES)})",
                "offset": str(offset), "limit": "10000"})
    if r is None: break
    try:
        data = r.json()
    except Exception:
        break
    if not isinstance(data, list) or not data: break
    for d in data:
        existing_tickers.add((d["ticker"], d["exchange"]))
    offset += 10000
    if len(data) < 10000: break

before_count = len(all_stocks)
all_stocks = [s for s in all_stocks if (s["ticker"], s["exchange"]) not in existing_tickers]
print(f"  Titoli con storico gia' presente: {before_count - len(all_stocks)} — saltati")
print(f"  Titoli da ricostruire: {len(all_stocks)}")

# ── 2. CANCELLA E RICOSTRUISCE 5 ANNI PER OGNI TITOLO ────────
print(f"\n[2/2] Ricostruzione storico 5 anni ({len(all_stocks)} titoli)...")
ok = fail = 0
t0 = time.time()
for i, stock in enumerate(all_stocks):
    ticker = stock["ticker"]
    exchange = stock["exchange"]
    lt = leeway_ticker(ticker, exchange, stock.get("primary_exchange") or "")
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
    resp = safe_get(url)
    data_l = None
    if resp is not None and resp.status_code == 200:
        try:
            data_l = resp.json()
        except Exception:
            data_l = None
    # Fallback Corea: se la classificazione KOSE/KOSDAQ non e' esatta,
    # prova l'altro suffisso (.KO <-> .KQ) prima di dichiarare fail
    if (not isinstance(data_l, list) or not data_l) and exchange == "KRX":
        alt = lt[:-3] + (".KO" if lt.endswith(".KQ") else ".KQ")
        url_kr = f"{LEEWAY_BASE}/historicalquotes/{alt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
        resp = safe_get(url_kr)
        if resp is not None and resp.status_code == 200:
            try:
                data_l = resp.json()
            except Exception:
                data_l = None
    # Fallback Germania: .XETRA a volte non trova titoli minori, .F spesso si
    if (not isinstance(data_l, list) or not data_l) and exchange == "XETRA":
        lt = ticker.rstrip(".") + ".F"
        url2 = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TODAY}"
        resp = safe_get(url2)
        if resp is not None and resp.status_code == 200:
            try:
                data_l = resp.json()
            except Exception:
                data_l = None
    if not isinstance(data_l, list) or not data_l:
        fail += 1
        continue

    rows = []
    for row in data_l:
        adj = row.get("adjusted_close") or row.get("close")
        if adj is None: continue
        rows.append({"ticker": ticker, "exchange": exchange,
                      "date": row["date"], "adj_close": float(adj)})
    if not rows:
        fail += 1
        continue

    # Cancella lo storico esistente per questo titolo (rimuove eventuale
    # contaminazione Yahoo/Leeway mescolata) prima di riscrivere quello pulito
    safe_delete(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})

    for j in range(0, len(rows), 500):
        safe_post(SUPABASE_URL + "/rest/v1/prices_eod", rows[j:j+500], headers=headers_up)

    ok += 1
    if (i + 1) % 100 == 0:
        elapsed = time.time() - t0
        print(f"    ... {i+1}/{len(all_stocks)} processati ({elapsed/60:.0f} min trascorsi) — ok={ok} fail={fail}")
    time.sleep(0.4)

print(f"\n  Ricostruiti: ok={ok} fail={fail} su {len(all_stocks)} titoli")
print("\n" + "=" * 60)
print(f"REBUILD 5 ANNI {REGION} COMPLETATO in {(time.time()-t0)/60:.0f} min")
print("=" * 60)
