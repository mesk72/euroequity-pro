import os, requests, csv, io, math, time
from datetime import datetime, timedelta

# ============================================================
# DEBUG AS (Amsterdam): quali titoli olandesi nei top 100 per
# mkt cap NON hanno prezzo su Leeway con .AS, e quali suffissi
# alternativi funzionano (.F, .XETRA, .BR, .PA)
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

def leeway_righe(lt, from_d, to_d):
    """Ritorna il numero di righe (con retry per errori transitori)."""
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return len(data) if isinstance(data, list) else 0
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1)); continue
            return 0
        except Exception:
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return 0

to_d   = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

print("=" * 60)
print("[1] TOP CANDIDATI AS (ENXTAM) DAL TIKR EU")
print("=" * 60)

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"TIKR EU: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
candidati = []
for row in reader:
    if row.get("Primary Exchange","").strip() != "ENXTAM": continue
    ticker  = row.get("Ticker","").strip()
    company = row.get("Company Name","").strip()
    if is_excluded(company): continue
    mc = parse_mktcap(row.get("Last Mkt Cap",""))
    candidati.append((ticker, company, mc or 0))
candidati.sort(key=lambda x: x[2], reverse=True)
print(f"Candidati AS (esclusi ETF/fondi): {len(candidati)}")

# Verifica i primi 115 con .AS — bastano per capire chi manca nei top 100
N_TEST = 115
print()
print("=" * 60)
print(f"[2] CHECK .AS SUI PRIMI {N_TEST} PER MKT CAP")
print("=" * 60)
falliti = []
ok = 0
for ticker, company, mc in candidati[:N_TEST]:
    lt = ticker.rstrip(".") + ".AS"
    n = leeway_righe(lt, from_d, to_d)
    if n > 0:
        ok += 1
    else:
        falliti.append((ticker, company, mc))
        print(f"  SENZA PREZZO: {ticker} ({company}) mkt_cap={mc:,.0f}MM")
    time.sleep(0.1)
print(f"\n  OK con .AS: {ok}/{N_TEST} — falliti: {len(falliti)}")

print()
print("=" * 60)
print("[3] TEST SUFFISSI ALTERNATIVI SUI FALLITI")
print("=" * 60)
ALT_SUFFIXES = [".F", ".XETRA", ".BR", ".PA"]
for ticker, company, mc in falliti:
    base = ticker.rstrip(".")
    print(f"\n  {ticker} — {company} (mkt_cap={mc:,.0f}MM)")
    trovato = False
    for suf in ALT_SUFFIXES:
        n = leeway_righe(base + suf, from_d, to_d)
        if n > 0:
            print(f"    {base}{suf}: righe={n}  <-- FUNZIONA")
            trovato = True
        else:
            print(f"    {base}{suf}: righe=0")
        time.sleep(0.1)
    if not trovato:
        print(f"    NESSUN SUFFISSO ALTERNATIVO FUNZIONA")

print()
print("=" * 60)
print("[4] CONFRONTO CON DB: AS in_universe attuali")
print("=" * 60)
headers_count = {**headers_r, "Prefer": "count=exact"}
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select": "ticker", "in_universe": "eq.true", "exchange": "eq.AS", "limit": "1"})
print(f"  AS in_universe (DB): {r.headers.get('content-range')}")
