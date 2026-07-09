import os, time, re, requests
from datetime import datetime

# ============================================================
# FORWARDALPHA — BETA (Yahoo Finance) + RISK-FREE RATE US
# Scarica il campo "beta" precalcolato da Yahoo (5 anni mensile,
# contro S&P 500 — metodologia standard Yahoo) per tutti i titoli
# US in universo, usando yahoo_ticker gia' presente nel database.
# Scarica anche il rendimento del Treasury 10Y (^TNX) come risk-free
# rate di riferimento per il mercato USA.
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance — aggiungere 'pip install yfinance' nel workflow")


def safe_get(url, **kwargs):
    for attempt in range(3):
        try:
            return requests.get(url, timeout=kwargs.pop("timeout", 20), **kwargs)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1)); continue
            print(f"  WARN GET fallita: {e}")
            return None


print("=" * 60)
print("BETA (Yahoo Finance) + RISK-FREE RATE (US Treasury, fonte ufficiale)")
print("=" * 60)

# ── 1. RISK-FREE RATE: Treasury 10Y — direttamente dal Tesoro USA, non
# da Yahoo. Fonte pubblica ufficiale, nessuna chiave richiesta, nessun
# problema di licenza/ToS: home.treasury.gov/.../pages/xml
print("\n[1/2] Scarico rendimento Treasury 10Y da fonte ufficiale (Tesoro USA)...")
risk_free_10y = None
try:
    year = datetime.now().year
    url = (f"https://home.treasury.gov/resource-center/data-chart-center/"
           f"interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}")
    resp = requests.get(url, timeout=20)
    if resp.status_code == 200:
        # Ultima voce nel feed = data piu' recente disponibile
        dates_rates = re.findall(
            r'<d:NEW_DATE[^>]*>([^<]+)</d:NEW_DATE>.*?<d:BC_10YEAR[^>]*>([^<]+)</d:BC_10YEAR>',
            resp.text, re.DOTALL)
        if dates_rates:
            last_date, last_rate = dates_rates[-1]
            risk_free_10y = round(float(last_rate), 4)
            print(f"  Treasury 10Y: {risk_free_10y}% (data: {last_date[:10]}, fonte: home.treasury.gov)")
        else:
            print("  WARN: nessuna voce trovata nel feed del Tesoro")
    else:
        print(f"  WARN: HTTP {resp.status_code} dal Tesoro")
except Exception as e:
    print(f"  WARN lettura feed Tesoro: {e}")

if risk_free_10y is not None:
    # Salva in una piccola tabella macro_rates (va creata se non esiste, vedi nota)
    try:
        r = requests.post(SUPABASE_URL + "/rest/v1/macro_rates", headers=headers_up,
            json={"region": "US", "rate_10y": risk_free_10y,
                  "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00")})
        if r.status_code not in (200, 201, 204):
            print(f"  WARN salvataggio macro_rates: HTTP {r.status_code} — {r.text[:200]}")
            print("  (probabile causa: la tabella 'macro_rates' non esiste ancora su Supabase)")
    except Exception as e:
        print(f"  WARN salvataggio macro_rates: {e}")

# ── 2. UNIVERSO US: legge ticker + yahoo_ticker ─────────────
print("\n[2/2] Caricamento universo US e download Beta...")
all_stocks = []
offset = 0
while True:
    r = safe_get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,yahoo_ticker", "in_universe": "eq.true",
                "exchange": "eq.US", "offset": str(offset), "limit": "1000"})
    if r is None: break
    try:
        data = r.json()
    except Exception:
        break
    if not isinstance(data, list) or not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break

print(f"  Titoli US in universo: {len(all_stocks)}")

ok = fail = skip_no_yahoo = 0
beta_batch = []
website_batch = []
t0 = time.time()

for i, stock in enumerate(all_stocks):
    ticker = stock["ticker"]
    exchange = stock["exchange"]
    # Fallback: se yahoo_ticker non e' popolato (es. titoli appena inseriti),
    # usa il ticker stesso (US: '.' -> '-', es. BRK.B -> BRK-B)
    yahoo_ticker = stock.get("yahoo_ticker") or ticker.replace(".", "-")

    try:
        info = yf.Ticker(yahoo_ticker).info
        beta = info.get("beta")
        website = info.get("website")
        if beta is None:
            fail += 1
        else:
            beta_batch.append({"ticker": ticker, "exchange": exchange, "beta": round(float(beta), 3)})
            ok += 1
        if website:
            website_batch.append({"ticker": ticker, "exchange": exchange, "website": website})
    except Exception as e:
        fail += 1
        if fail <= 5:
            print(f"    WARN {ticker} ({yahoo_ticker}): {e}")

    if len(beta_batch) >= 100:
        rr = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=beta_batch)
        if rr.status_code not in (200, 201, 204):
            print(f"    WARN salvataggio batch beta: HTTP {rr.status_code} — {rr.text[:200]}")
        beta_batch = []

    if len(website_batch) >= 100:
        rw = requests.post(SUPABASE_URL + "/rest/v1/stocks", headers=headers_up, params={"on_conflict":"ticker,exchange"}, json=website_batch)
        if rw.status_code not in (200, 201, 204):
            print(f"    WARN salvataggio batch website: HTTP {rw.status_code} — {rw.text[:200]}")
        website_batch = []

    if (i + 1) % 200 == 0:
        elapsed = time.time() - t0
        print(f"    ... {i+1}/{len(all_stocks)} processati ({elapsed/60:.1f} min) — ok={ok} fail={fail}")

    time.sleep(0.3)  # rate limiting Yahoo

if beta_batch:
    rr = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=beta_batch)
    if rr.status_code not in (200, 201, 204):
        print(f"  WARN salvataggio ultimo batch beta: HTTP {rr.status_code} — {rr.text[:200]}")
if website_batch:
    rw = requests.post(SUPABASE_URL + "/rest/v1/stocks", headers=headers_up, params={"on_conflict":"ticker,exchange"}, json=website_batch)
    if rw.status_code not in (200, 201, 204):
        print(f"  WARN salvataggio ultimo batch website: HTTP {rw.status_code} — {rw.text[:200]}")

print(f"\n  Beta salvati: ok={ok} fail={fail} su {len(all_stocks)}")
print("\n" + "=" * 60)
print(f"COMPLETATO in {(time.time()-t0)/60:.1f} min")
print("=" * 60)
