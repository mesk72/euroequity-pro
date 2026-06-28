import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

MIN_PRICE_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]
EXCLUDE_NAMES = [
    "ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()
    return any(kw in name for kw in EXCLUDE_NAMES)

def load_exchange(exchange):
    stocks = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,company,sector,mkt_cap,in_universe",
                    "exchange": f"eq.{exchange}",
                    "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return stocks

def check_prices(stocks, exchange):
    no_price = []
    for s in stocks:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date", "ticker": f"eq.{s['ticker']}",
                    "exchange": f"eq.{exchange}",
                    "date": f"gte.{MIN_PRICE_DATE}", "limit": "1"})
        rows = r.json()
        if not isinstance(rows, list) or not rows:
            no_price.append(s["ticker"])
    return no_price

print(f"=== SIMULAZIONE NUOVO UNIVERSO ===")
print(f"Verifica prezzi: >= {MIN_PRICE_DATE}")
print()

# EU grandi — mkt_cap >= 500M
print("--- BORSE GRANDI: mkt_cap >= $500M ---")
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    no_price = check_prices(eligible, ex)
    print(f"{ex:<8} eligible={len(eligible):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price}")

print()

# EU medie — top 100
print("--- BORSE MEDIE: top 100 ---")
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    stocks = load_exchange(ex)
    eligible = sorted(
        [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
        key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:100]
    no_price = check_prices(eligible, ex)
    print(f"{ex:<8} eligible={len(eligible):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price}")

print()

# EU piccole — tutti
print("--- BORSE PICCOLE: tutti ---")
for ex in ["VI","IR","LS"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    no_price = check_prices(eligible, ex)
    print(f"{ex:<8} eligible={len(eligible):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price}")

print()

# US — top 2000
print("--- US: top 2000 ---")
stocks = load_exchange("US")
eligible = sorted(
    [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
    key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:2000]
no_price = check_prices(eligible, "US")
print(f"US       eligible={len(eligible):>5} senza_prezzo={len(no_price):>4}")
if no_price:
    print(f"         SENZA PREZZO: {no_price}")

print()

# TSX — top 400
print("--- TSX: top 400 ---")
stocks = load_exchange("TSX")
eligible = sorted(
    [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
    key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:400]
no_price = check_prices(eligible, "TSX")
print(f"TSX      eligible={len(eligible):>5} senza_prezzo={len(no_price):>4}")
if no_price:
    print(f"         SENZA PREZZO: {no_price}")

print()
print("=== NESSUNA MODIFICA AL DB ===")
