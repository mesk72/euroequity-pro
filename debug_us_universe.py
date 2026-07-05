import os, requests, csv, io, time

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

SPECIAL_TICKERS_US = {"BRK.A": "BRK-B"}

def leeway_ticker(ticker, exchange):
    if exchange == "TSX":
        return ticker.replace(".", "-") + ".TO"
    if ticker in SPECIAL_TICKERS_US:
        return SPECIAL_TICKERS_US[ticker] + ".US"
    return ticker.rstrip(".").replace(".", "-") + ".US"

def parse_num(v):
    if not v: return None
    s = str(v).strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True; s = s[1:-1]
    s = s.replace('$','').replace('x','').replace('%','').strip()
    for suf in ['USDMM','EURMM','MM','B','bn']:
        s = s.replace(suf,'').strip()
    if s in ['-','','N/A','nm']: return None
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

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS","GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND","SAVINGS ACCOUNT FUND",
    "CASH FUND","CASH MANAGEMENT FUND","HIGH INTEREST SAVINGS",
    "3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED"," LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE","XTRACKERS","LYXOR","VANGUARD ETF",
    "AMUNDI ETF","SPDR ETF","SPDR GOLD","ISHARES","WISDOMTREE ETF","VANECK ETF",
    "INDEX FUND","BOND FUND","MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
]
def is_excluded(company):
    name = (company or "").upper()
    return any(kw in name for kw in ALWAYS_EXCLUDE)

print("Carico TIKR NA...")
r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
candidati = []
for row in reader:
    ticker = row.get("Ticker", "").strip()
    if not ticker: continue
    exch_raw = (row.get("Exchange", "") or row.get("Market", "")).strip().upper()
    exchange = "TSX" if exch_raw in ("TSX", "TSXV", "TO") else "US"
    if exchange != "US": continue
    company = row.get("Company Name", "").strip()
    if is_excluded(company): continue
    mc = parse_num(row.get("Last Mkt Cap", ""))
    candidati.append((ticker, mc or 0))

candidati.sort(key=lambda x: x[1], reverse=True)
print(f"Candidati US totali: {len(candidati)}")

print("\nVerifico presenza Leeway sui primi 2100 candidati per mkt cap (per vedere cosa fallisce)...")
eligible = 0
falliti = []
for i, (ticker, mc) in enumerate(candidati[:2100]):
    lt = leeway_ticker(ticker, "US")
    try:
        url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from=2026-06-01&to=2026-07-05"
        resp = requests.get(url, timeout=15)
        ok = resp.status_code == 200 and isinstance(resp.json(), list) and len(resp.json()) > 0
    except Exception as e:
        ok = False
    if ok:
        eligible += 1
    else:
        falliti.append((ticker, lt, mc))
    if eligible >= 2000:
        print(f"Raggiunti 2000 eligible dopo aver controllato {i+1} candidati")
        break
    time.sleep(0.05)

print(f"\nEligible raggiunti: {eligible}")
print(f"Falliti nel frattempo: {len(falliti)}")
for t, lt, mc in falliti:
    print(f"  {t} (leeway={lt}, mktcap={mc:.0f})")
