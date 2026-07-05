import os, requests, csv, io, time
from datetime import datetime, timedelta

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

def ha_prezzo_su_leeway(ticker, exchange):
    to_d = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    lt = leeway_ticker(ticker, exchange)
    try:
        url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return True, lt
    except Exception as e:
        return False, f"ERR:{e}"
    return False, lt

def parse_mktcap(v):
    if not v: return None
    s = str(v).strip().replace("$", "").strip()
    for suf in ("USDMM", "EURMM", "MM"):
        s = s.replace(suf, "")
    s = s.strip()
    if not s or s in ("-", "N/A", "nm"): return None
    s = s.replace(",", "")
    try:
        f = float(s)
        return f if f > 0 else None
    except: return None

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS","GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND","SAVINGS ACCOUNT FUND",
    "CASH FUND","CASH MANAGEMENT FUND","HIGH INTEREST SAVINGS","3X LEVERAGED",
    "2X LEVERAGED","-1X LEVERAGED"," LEVERAGED","EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF","SPDR ETF","SPDR GOLD","ISHARES",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND","MUTUAL FUND","MUTUALFUND",
    "INVESCO DB ","SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
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
    ex_raw = row.get("Primary Exchange", "").strip().upper()
    if ex_raw in ("TSX", "TSXV", "TO"): continue  # solo US qui
    company = row.get("Company Name", "").strip()
    mc = parse_mktcap(row.get("Last Mkt Cap", ""))
    if is_excluded(company): continue
    if mc: candidati.append((ticker, company, mc))

candidati.sort(key=lambda x: x[2], reverse=True)
print(f"Candidati US totali (post esclusione ETF): {len(candidati)}")

print("\nVerifico Leeway sui primi 2050 per market cap...")
ok = 0
falliti = []
for i, (ticker, company, mc) in enumerate(candidati[:2050]):
    trovato, lt = ha_prezzo_su_leeway(ticker, "US")
    if trovato:
        ok += 1
    else:
        falliti.append((ticker, company, mc, lt))
    if ok >= 2000:
        print(f"Raggiunti 2000 titoli validi dopo aver controllato {i+1} candidati")
        break
    time.sleep(0.1)

print(f"\nOK={ok}  FALLITI finora={len(falliti)}")
print("\nLista completa falliti (ticker, azienda, mkt_cap, leeway_ticker_provato):")
for t, c, mc, lt in falliti:
    print(f"  {t:<8} {c[:40]:<40} mktcap={mc:>12,.0f}  leeway={lt}")
