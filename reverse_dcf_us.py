import csv, requests, math, os, io, time
from datetime import datetime, timedelta

# ============================================================
# FORWARDALPHA — REVERSE EARNINGS MODEL (US)
# Implied growth a 10 anni (bisection, gTV=2.5%) confrontato con
# la crescita EPS forward 12-24m e 24-36m (stessa calendarizzazione
# gia' verificata in weekly_us.py, estesa con due anni fiscali in piu').
# Ke = Rf(Treasury 10Y) + Beta*ERP(5%). Serve macro_rates e
# fundamentals.beta gia' popolati (fetch_beta_us.py).
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY_DT     = datetime.now()
ERP          = 0.05
G_TERMINAL   = 0.025
YEARS        = 10

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}


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
    s = s.replace('$','').replace('x','').replace('%','').strip()
    for suf in ['USDMM','EURMM','MM','B','bn']:
        s = s.replace(suf,'').strip()
    if s in ['-','','N/A','nm',chr(8212)]: return None
    if ',' in s and '.' in s:
        s = s.replace('.','').replace(',','.')
    elif ',' in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',','.')
        else:
            s = s.replace(',','')
    try:
        f = float(s)
        return -f if negative else f
    except: return None


def implied_growth_bisection(price, eps_ntm, ke, g_terminal=G_TERMINAL, years=YEARS, tol=1e-6, max_iter=200):
    if price is None or eps_ntm is None or eps_ntm <= 0 or ke is None or ke <= g_terminal:
        return None

    def dcf_value(g):
        pv = 0.0
        for t in range(1, years + 1):
            pv += eps_ntm * (1 + g) ** t / (1 + ke) ** t
        eps_terminal = eps_ntm * (1 + g) ** years
        tv = eps_terminal * (1 + g_terminal) / (ke - g_terminal)
        pv += tv / (1 + ke) ** years
        return pv

    lo, hi = -0.50, 1.00
    if dcf_value(lo) > price: return None
    if dcf_value(hi) < price: return None
    mid = 0.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        val = dcf_value(mid)
        if abs(val - price) < tol:
            return mid
        if val < price:
            lo = mid
        else:
            hi = mid
    return mid


def get_fy_month(ticker, exchange):
    return fy_map.get((ticker, exchange), 12)


def calendarize_full(ticker, exchange, fy_values, today_dt):
    """fy_values: dict {anno: eps} con chiavi 2025..2030.
    Ritorna ltm, ntm, fwd24, fwd36, w_curr, w_next."""
    fm = get_fy_month(ticker, exchange)
    last_day = 28 if fm == 2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year - 1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        fy_end = datetime(fy_end.year - 1, fm, last_day)
        pub_date = fy_end + timedelta(days=60)

    v0 = fy_values.get(fy_end.year)
    v1 = fy_values.get(fy_end.year + 1)
    v2 = fy_values.get(fy_end.year + 2)
    v3 = fy_values.get(fy_end.year + 3)
    v4 = fy_values.get(fy_end.year + 4)

    next_pub = datetime(pub_date.year + 1, pub_date.month, pub_date.day)
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next

    def blend(a, b):
        return w_curr * a + w_next * b if a is not None and b is not None else None

    ltm   = blend(v0, v1)
    ntm   = blend(v1, v2)
    fwd24 = blend(v2, v3)
    fwd36 = blend(v3, v4)
    return ltm, ntm, fwd24, fwd36, w_curr, w_next


print("=" * 60)
print("REVERSE EARNINGS MODEL — US")
print("=" * 60)

# ── 1. RISK-FREE RATE US ─────────────────────────────────────
print("\n[1/4] Lettura risk-free rate US da macro_rates...")
risk_free = None
try:
    r = requests.get(SUPABASE_URL + "/rest/v1/macro_rates", headers=headers_r,
        params={"select": "rate_10y", "region": "eq.US"})
    data = r.json()
    if isinstance(data, list) and data:
        risk_free = float(data[0]["rate_10y"]) / 100  # da percentuale a decimale
        print(f"  Risk-free US (Treasury 10Y): {risk_free:.4%}")
except Exception as e:
    print(f"  ERRORE lettura macro_rates: {e}")

if risk_free is None:
    raise SystemExit("Risk-free rate US non trovato in macro_rates — impossibile procedere")

# ── 2. FISCAL YEAR END PER TICKER ────────────────────────────
print("\n[2/4] Lettura fiscal_year_end.csv...")
TIKR_FY_EXCHANGE_MAP = {
    "NasdaqGS": "US", "NasdaqGM": "US", "NasdaqCM": "US",
    "NYSE": "US", "NYSEAM": "US", "ARCA": "US", "BATS": "US",
    "OTCPK": "US", "CNSX": "US", "TSXV": "TSX",
}
def _norm_fy_exchange(raw):
    return TIKR_FY_EXCHANGE_MAP.get(raw, raw)

fy_map = {}
try:
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
    reader = csv.DictReader(io.StringIO(r.text))
    for row in reader:
        ticker = row["ticker"].strip()
        exchange = _norm_fy_exchange(row["exchange"].strip())
        month = parse_num(row.get("fiscal_month", "12"))
        fy_map[(ticker, exchange)] = int(month) if month else 12
    print(f"  Fiscal year end caricati: {len(fy_map)}")
except Exception as e:
    print(f"  WARN lettura fiscal_year_end.csv: {e} — uso default dicembre per tutti")

# ── 3. TIKR NA: EPS FY2025-FY2030 ────────────────────────────
print("\n[3/4] Lettura TIKR NA (EPS FY2025-FY2030)...")
eps_by_ticker = {}
try:
    r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
    reader = csv.DictReader(io.StringIO(r.text))
    for row in reader:
        ticker = row.get("Ticker", "").strip()
        if not ticker: continue
        exch_raw = (row.get("Exchange", "") or row.get("Market", "")).strip().upper()
        exchange = "TSX" if exch_raw in ("TSX", "TSXV", "TO", "TSE") else "US"
        fy_values = {
            2025: parse_num(row.get("EPS Normalized (FY 2025)", "")),
            2026: parse_num(row.get("Mean EPS Normalized (FY 2026)", "")),
            2027: parse_num(row.get("Mean EPS Normalized (FY 2027)", "")),
            2028: parse_num(row.get("Mean EPS Normalized (FY 2028)", "")),
            2029: parse_num(row.get("Mean EPS Normalized (FY 2029)", "")),
            2030: parse_num(row.get("Mean EPS Normalized (FY 2030)", "")),
        }
        eps_by_ticker[(ticker, exchange)] = fy_values
    print(f"  Titoli con dati EPS: {len(eps_by_ticker)}")
except Exception as e:
    raise SystemExit(f"Errore lettura TIKR NA: {e}")

# ── 4. UNIVERSO US: price + beta, calcolo completo ──────────
print("\n[4/4] Calcolo per ogni titolo US in universo...")
all_stocks = []
offset = 0
while True:
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange", "in_universe": "eq.true",
                    "exchange": "eq.US", "offset": str(offset), "limit": "1000"}, timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  WARN lettura universo: {e}"); break
    if not isinstance(data, list) or not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break

print(f"  Titoli US in universo: {len(all_stocks)}")

# Carica price+beta in blocco (una volta sola, non un titolo alla volta)
print("  Carico price+beta in blocco da fundamentals...")
fund_map = {}
offset = 0
while True:
    try:
        r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
            params={"select": "ticker,exchange,price,beta", "exchange": "eq.US",
                    "offset": str(offset), "limit": "1000"}, timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  WARN lettura fundamentals offset {offset}: {e}"); break
    if not isinstance(data, list) or not data: break
    for d in data:
        fund_map[(d["ticker"], d["exchange"])] = d
    offset += 1000
    if len(data) < 1000: break
print(f"  Price+beta disponibili per {len(fund_map)} titoli")

updates = []
ok = skip_no_eps = skip_no_price_beta = skip_bisection_fail = 0
esempi = []

for i, stock in enumerate(all_stocks):
    ticker, exchange = stock["ticker"], stock["exchange"]
    fy_values = eps_by_ticker.get((ticker, exchange))
    if not fy_values:
        skip_no_eps += 1
        continue

    ltm, ntm, fwd24, fwd36, w_curr, w_next = calendarize_full(ticker, exchange, fy_values, TODAY_DT)
    if ntm is None:
        skip_no_eps += 1
        continue

    fdata = fund_map.get((ticker, exchange))
    if not fdata:
        skip_no_price_beta += 1
        continue
    price = fdata.get("price")
    beta  = fdata.get("beta")
    if price is None or beta is None:
        skip_no_price_beta += 1
        continue

    ke = risk_free + float(beta) * ERP
    implied_g = implied_growth_bisection(float(price), ntm, ke)
    if implied_g is None:
        skip_bisection_fail += 1

    growth_12_24 = (fwd24 / ntm - 1) if (fwd24 is not None and ntm) else None
    growth_24_36 = (fwd36 / fwd24 - 1) if (fwd36 is not None and fwd24) else None
    cagr_2y = None
    if growth_12_24 is not None and growth_24_36 is not None:
        product = (1 + growth_12_24) * (1 + growth_24_36)
        cagr_2y = math.sqrt(product) - 1 if product > 0 else None

    upd = {
        "ticker": ticker, "exchange": exchange,
        "eps_fwd24": round(fwd24, 4) if fwd24 is not None else None,
        "eps_fwd36": round(fwd36, 4) if fwd36 is not None else None,
        "eps_growth_12_24m": round(growth_12_24, 4) if growth_12_24 is not None else None,
        "eps_growth_24_36m": round(growth_24_36, 4) if growth_24_36 is not None else None,
        "eps_cagr_2y": round(cagr_2y, 4) if cagr_2y is not None else None,
        "implied_growth_10y": round(implied_g, 4) if implied_g is not None else None,
        "ke": round(ke, 4),
        "eps_ntm_dcf": round(ntm, 4),
    }
    updates.append(upd)
    ok += 1

    if len(esempi) < 10 and implied_g is not None and cagr_2y is not None:
        esempi.append((ticker, price, ntm, beta, ke, implied_g, cagr_2y))

    if len(updates) >= 100:
        rr = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=updates)
        if rr.status_code not in (200, 201, 204):
            print(f"    WARN salvataggio batch: HTTP {rr.status_code} — {rr.text[:200]}")
        updates = []

    if (i + 1) % 300 == 0:
        print(f"    ... {i+1}/{len(all_stocks)} processati")

if updates:
    rr = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=updates)
    if rr.status_code not in (200, 201, 204):
        print(f"  WARN salvataggio ultimo batch: HTTP {rr.status_code} — {rr.text[:200]}")

print(f"\n  Calcolati: ok={ok}  skip_no_eps={skip_no_eps}  skip_no_price_beta={skip_no_price_beta}  bisection_fallita={skip_bisection_fail}")

print("\n" + "=" * 60)
print("ESEMPI (primi 10 con dati completi)")
print("=" * 60)
print(f"{'Ticker':<8} {'Prezzo':>8} {'EPS_NTM':>8} {'Beta':>6} {'Ke':>7} {'Implied G':>10} {'CAGR 2y':>9}")
for ticker, price, ntm, beta, ke, implied_g, cagr_2y in esempi:
    print(f"{ticker:<8} {price:>8.2f} {ntm:>8.2f} {beta:>6.2f} {ke:>6.2%} {implied_g:>9.2%} {cagr_2y:>8.2%}")

print("\n" + "=" * 60)
print("COMPLETATO")
print("=" * 60)
