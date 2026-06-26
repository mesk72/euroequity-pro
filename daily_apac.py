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
YESTERDAY    = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
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
print(f"  Scarico prezzi da Leeway per {{len(all_stocks)}} titoli...")
for stock in all_stocks:
    ticker   = stock['ticker']
    exchange = stock['exchange']
    # Leggi ultima data disponibile nel DB
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={{"select": "date", "ticker": f"eq.{{ticker}}",
                "exchange": f"eq.{{exchange}}", "order": "date.desc", "limit": "1"}})
    row = r.json()
    last = row[0]["date"] if isinstance(row, list) and row else "2021-01-01"
    if last >= TODAY:
        ok_leeway += 1
        continue
    start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    lt = ticker + LEEWAY_SUFFIX.get(exchange, "")
    url = f"{{LEEWAY_BASE}}/historicalquotes/{{lt}}?apitoken={{LEEWAY_KEY}}&from={{start_dt}}&to={{TODAY}}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200: fail_leeway += 1; continue
        data_l = resp.json()
        if not isinstance(data_l, list) or not data_l: fail_leeway += 1; continue
        for row2 in data_l:
            adj = row2.get('adjusted_close') or row2.get('close')
            if adj is None: continue
            price_buf.append({{
                "ticker": ticker, "exchange": exchange,
                "date": row2['date'], "adj_close": float(adj),
            }})
        ok_leeway += 1
    except: fail_leeway += 1
    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        price_buf = []
    time.sleep(0.05)
if price_buf:
    requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
print(f"  Prezzi Leeway: ok={{ok_leeway}} fail={{fail_leeway}}")
ok_prices = ok_leeway; fail_prices = fail_leeway