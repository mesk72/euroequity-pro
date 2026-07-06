import os, requests, csv, io, math, time
from datetime import datetime, timedelta

# ============================================================
# FIX UNIVERSO AS (Amsterdam) — mirato, senza toccare il resto EU
# Top 100 per mkt cap tra chi ha prezzo su Leeway (realistico: 98).
# Per i titoli nuovi scarica anche lo storico 5 anni in prices_eod.
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}
headers_count = {**headers_r, "Prefer": "count=exact"}

TODAY   = datetime.now().strftime("%Y-%m-%d")
FROM_5Y = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
TOP_N   = 100

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED"," LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES","WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI","ISHARES MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
    "PARTICIPATIES","PARAPLUFONDS","MICROKREDIETFONDS",
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
    s = s.replace(",","")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

def leeway_data(lt, from_d, to_d):
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else []
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1)); continue
            return []
        except Exception:
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return []

to_d   = TODAY
from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

print("=" * 60)
print("FIX UNIVERSO AS — top 100 con prezzo Leeway")
print("=" * 60)

# ── 1. Candidati TIKR ─────────────────────────────────────────
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"TIKR EU: HTTP {r.status_code}")
reader = csv.DictReader(io.StringIO(r.text))
candidati = []
for row in reader:
    if row.get("Primary Exchange","").strip() != "ENXTAM": continue
    ticker  = row.get("Ticker","").strip()
    company = row.get("Company Name","").strip()
    if is_excluded(company): continue
    sector  = row.get("Sector","").strip()
    mc = parse_mktcap(row.get("Last Mkt Cap",""))
    candidati.append((ticker, company, sector, mc or 0))
candidati.sort(key=lambda x: x[3], reverse=True)
print(f"Candidati AS (dopo filtro fondi aggiornato): {len(candidati)}")

# ── 2. Eligible: scorri per mkt cap, tieni chi ha prezzo ─────
eligible = []
for ticker, company, sector, mc in candidati:
    if len(eligible) >= TOP_N: break
    if leeway_data(ticker.rstrip(".") + ".AS", from_d, to_d):
        eligible.append((ticker, company, sector, mc))
    time.sleep(0.1)
print(f"Eligible con prezzo Leeway: {len(eligible)} (target {TOP_N})")

# ── 3. Stato attuale DB ──────────────────────────────────────
stocks_db = {}
in_universe_db = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,in_universe","exchange":"eq.AS",
                "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch:
        stocks_db[s["ticker"]] = s
        if s.get("in_universe"): in_universe_db.add(s["ticker"])
    offset += 1000
    if len(batch)<1000: break
print(f"Nel DB: {len(stocks_db)} titoli AS, in_universe: {len(in_universe_db)}")

eligible_tickers = [t for t,_,_,_ in eligible]
nuovi = [t for t in eligible_tickers if t not in in_universe_db]
rimossi = [t for t in in_universe_db if t not in eligible_tickers]
print(f"Da aggiungere: {nuovi}")
print(f"Uscirebbero dal top 100: {rimossi}")

# ── 4. Inserisci titoli mancanti in stocks ───────────────────
new_stocks = []
for ticker, company, sector, mc in eligible:
    if ticker not in stocks_db:
        new_stocks.append({
            "ticker": ticker, "exchange": "AS", "company": company,
            "sector": sector, "country": "NLD", "flag": "🇳🇱",
            "currency": "EUR", "in_universe": False,
            "primary_exchange": "ENXTAM",
        })
if new_stocks:
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_ins, json=new_stocks)
    print(f"Inseriti {len(new_stocks)} nuovi titoli: HTTP {r2.status_code}")

# ── 5. Upsert mkt_cap in fundamentals ────────────────────────
mkt_updates = [{"ticker": t, "exchange": "AS", "mkt_cap": mc}
               for t,_,_,mc in eligible if mc]
for i in range(0, len(mkt_updates), 100):
    requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up, json=mkt_updates[i:i+100])

# ── 6. Reset e set in_universe (solo AS) ─────────────────────
requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
    params={"exchange":"eq.AS"}, json={"in_universe": False})
CHUNK = 100
for i in range(0, len(eligible_tickers), CHUNK):
    chunk = eligible_tickers[i:i+CHUNK]
    r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
        params={"ticker": "in.(" + ",".join(chunk) + ")", "exchange": "eq.AS"},
        json={"in_universe": True})
    if r2.status_code not in (200, 204):
        print(f"FAIL blocco {i}: {r2.status_code} {r2.text[:120]}")

# ── 7. Storico 5 anni per chi non ha dati in prices_eod ──────
print("\nStorico 5 anni per i titoli senza dati in prices_eod...")
for ticker in eligible_tickers:
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_count,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":"eq.AS","limit":"1"})
    cr = rc.headers.get("content-range","")
    tot = int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else 0
    if tot >= 100: continue  # ha gia' storico
    data_l = leeway_data(ticker.rstrip(".") + ".AS", FROM_5Y, TODAY)
    rows = []
    for row in data_l:
        adj = row.get("adjusted_close") or row.get("close")
        if adj is None: continue
        rows.append({"ticker": ticker, "exchange": "AS",
                     "date": row["date"], "adj_close": float(adj)})
    if not rows:
        print(f"  {ticker}: nessun dato storico!")
        continue
    for j in range(0, len(rows), 500):
        requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_up, json=rows[j:j+500])
    print(f"  {ticker}: scaricate {len(rows)} righe storico")
    time.sleep(0.4)

# ── 8. Verifica finale ───────────────────────────────────────
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","in_universe":"eq.true","exchange":"eq.AS","limit":"1"})
print(f"\nAS in_universe finale (DB): {r.headers.get('content-range')}")
print("FATTO.")
