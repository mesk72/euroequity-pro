import os, requests, csv, io, math, time

# ============================================================
# UNIVERSO GCC — schermata UNICA (non per paese), come richiesto.
# Fonte prezzi: YAHOO (non Leeway — copertura Golfo non ancora
# confermata da Leeway/Lars). Se in futuro Lars conferma ticker
# Leeway per queste borse, si potra' migrare come fatto altrove.
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}
headers_count = {**headers_r, "Prefer": "count=exact"}

TOP_N = 350
EXCHANGE = "GCC"  # un solo codice interno per tutte le borse del Golfo

# Mappa: Primary Exchange del file TIKR -> (suffisso Yahoo, country ISO3, bandiera)
GCC_MAP = {
    "SASE": (".SR", "SAU", "🇸🇦"),
    "DSM":  (".QA", "QAT", "🇶🇦"),
    "KWSE": (".KW", "KWT", "🇰🇼"),
    "ADX":  (".AE", "ARE", "🇦🇪"),
    "DFM":  (".AE", "ARE", "🇦🇪"),
    "DIFX": (".AE", "ARE", "🇦🇪"),
    "MSM":  (".OM", "OMN", "🇴🇲"),   # da verificare — copertura Yahoo incerta
    "BAX":  (".BH", "BHR", "🇧🇭"),   # da verificare — copertura Yahoo incerta
}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "CASH FUND","CASH MANAGEMENT FUND",
    "3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED"," LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","ISHARES","WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND",
    "SICAV","ICAV"," MSCI ","YOURINDEX",
]

def is_excluded(company):
    name = (company or "").upper()
    return any(kw in name for kw in ALWAYS_EXCLUDE)

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("$","").strip()
    for suf in ("USDMM","EURMM","MM"):
        s = s.replace(suf,"")
    s = s.strip()
    if not s or s in ("-","N/A","nm"): return None
    s = s.replace(",","")  # formato americano: virgola=migliaia
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

def _yahoo_ha_prezzo(yt):
    """Verifica prezzo su Yahoo con retry, come per gli altri mercati."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yt}?range=5d&interval=1d"
    headers_y = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers_y, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("chart", {}).get("result")
                if result and result[0].get("timestamp"):
                    return True
                return False  # 200 ma senza dati: definitivo
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1)); continue
            return False
        except Exception:
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return False

print("=" * 60)
print("UNIVERSO GCC — schermata unica")
print("=" * 60)

# ── 1. Candidati dal file TIKR ────────────────────────────────
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_gcc_latest.csv", headers=headers_r)
print(f"TIKR GCC: HTTP {r.status_code}")
reader = csv.DictReader(io.StringIO(r.text))
candidati = []
tikr = {}
excl_count = 0
for row in reader:
    prim_ex = row.get("Primary Exchange","").strip()
    if prim_ex not in GCC_MAP:
        print(f"  ATTENZIONE: exchange sconosciuto '{prim_ex}', riga saltata")
        continue
    ticker  = row.get("Ticker","").strip()
    company = row.get("Company Name","").strip()
    if is_excluded(company):
        excl_count += 1
        continue
    sector = row.get("Sector","").strip()
    mc = parse_mktcap(row.get("Last Mkt Cap",""))
    suffix, country, flag = GCC_MAP[prim_ex]
    candidati.append((ticker, mc or 0))
    tikr[ticker] = {"company": company, "sector": sector, "mktcap": mc or 0,
                     "country": country, "flag": flag, "yahoo_suffix": suffix,
                     "primary_exchange": prim_ex}

candidati.sort(key=lambda x: x[1], reverse=True)
print(f"Candidati totali: {len(candidati)} (esclusi fondi/ETF: {excl_count})")

# ── 2. Verifica prezzo Yahoo in ordine di mkt cap, fino a TOP_N ─
eligible = []
esclusi_no_prezzo = []
print(f"\nVerifico prezzo Yahoo (target {TOP_N})...")
for ticker, mc in candidati:
    if len(eligible) >= TOP_N: break
    info = tikr[ticker]
    yt = ticker + info["yahoo_suffix"]
    if _yahoo_ha_prezzo(yt):
        eligible.append(ticker)
    else:
        esclusi_no_prezzo.append((ticker, info["company"], info["primary_exchange"]))
    time.sleep(0.15)

print(f"Eligible con prezzo Yahoo: {len(eligible)}/{TOP_N}")
if esclusi_no_prezzo:
    print(f"Scartati per mancanza prezzo Yahoo ({len(esclusi_no_prezzo)}):")
    for t, c, ex in esclusi_no_prezzo[:30]:
        print(f"    {t} ({c}) — {ex}")

# ── 3. Stato attuale DB ──────────────────────────────────────
stocks_db = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{EXCHANGE}","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch: stocks_db.add(s["ticker"])
    offset += 1000
    if len(batch) < 1000: break
print(f"\nGia' presenti in stocks (exchange=GCC): {len(stocks_db)}")

# ── 4. Inserisci titoli mancanti ─────────────────────────────
new_stocks = []
for ticker in eligible:
    if ticker not in stocks_db:
        info = tikr[ticker]
        new_stocks.append({
            "ticker": ticker, "exchange": EXCHANGE, "company": info["company"],
            "sector": info["sector"], "country": info["country"], "flag": info["flag"],
            "currency": "USD", "in_universe": False,
            "primary_exchange": info["primary_exchange"],
            "yahoo_ticker": ticker + info["yahoo_suffix"],
        })
if new_stocks:
    for i in range(0, len(new_stocks), 100):
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_ins, json=new_stocks[i:i+100])
        if r2.status_code not in (200,201,204):
            print(f"  FAIL inserimento blocco {i}: {r2.status_code} {r2.text[:150]}")
    print(f"Inseriti {len(new_stocks)} nuovi titoli")

# ── 5. Mkt cap in fundamentals ───────────────────────────────
mkt_updates = [{"ticker": t, "exchange": EXCHANGE, "mkt_cap": tikr[t]["mktcap"]}
               for t in eligible if tikr[t]["mktcap"]]
for i in range(0, len(mkt_updates), 100):
    requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_up, json=mkt_updates[i:i+100])

# ── 6. Reset e imposta in_universe ───────────────────────────
requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
    params={"exchange": f"eq.{EXCHANGE}"}, json={"in_universe": False})
CHUNK = 100
ok = 0
for i in range(0, len(eligible), CHUNK):
    chunk = eligible[i:i+CHUNK]
    r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
        params={"ticker": "in.(" + ",".join(chunk) + ")", "exchange": f"eq.{EXCHANGE}"},
        json={"in_universe": True})
    if r2.status_code in (200, 204):
        ok += len(chunk)
    else:
        print(f"  FAIL blocco in_universe {i}: {r2.status_code} {r2.text[:150]}")

# ── 7. Riconciliazione riga-per-riga (stesso pattern usato per NA/EU) ─
r_check = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{EXCHANGE}","limit":"1000"})
actual_set = set(row["ticker"] for row in r_check.json()) if isinstance(r_check.json(),list) else set()
missing = [t for t in eligible if t not in actual_set]
if missing:
    print(f"Riconciliazione: {len(missing)} mancanti, correggo uno per uno...")
    for t in missing:
        rp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
            params={"ticker": f"eq.{t}", "exchange": f"eq.{EXCHANGE}"}, json={"in_universe": True})
        if rp.status_code not in (200,204):
            print(f"    ANCORA FALLITO {t}: {rp.status_code}")

# ── 8. Verifica finale dal DB ────────────────────────────────
r_final = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{EXCHANGE}","limit":"1"})
print(f"\n=== GCC in_universe finale (DB): {r_final.headers.get('content-range')} ===")
print(f"Atteso: {TOP_N}")
print("FATTO.")
