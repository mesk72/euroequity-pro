import os, requests
from datetime import datetime, timedelta
from collections import defaultdict

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

def get_tickers_with_prices(exchange):
    """Carica in bulk tutti i ticker con prezzi recenti per un exchange.
    Usa order=ticker per ottenere ticker distinti con paginazione affidabile."""
    tickers_with_price = set()
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "ticker",
                    "exchange": f"eq.{exchange}",
                    "date": f"gte.{MIN_PRICE_DATE}",
                    "order": "ticker.asc",
                    "limit": "2000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for row in batch:
            tickers_with_price.add(row["ticker"])
        offset += 2000
        if len(batch) < 2000: break
    return tickers_with_price

print(f"=== SIMULAZIONE NUOVO UNIVERSO ===")
print(f"Verifica prezzi: >= {MIN_PRICE_DATE}")
print()

# EU grandi — mkt_cap >= 500M
print("--- BORSE GRANDI: mkt_cap >= $500M ---")
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    stocks = load_exchange(ex)
    with_price = get_tickers_with_prices(ex)
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    no_price = [s["ticker"] for s in eligible if s["ticker"] not in with_price]
    print(f"{ex:<8} eligible={len(eligible):>5} con_prezzo={len(eligible)-len(no_price):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price[:30]}")

print()

# EU medie — top 100
print("--- BORSE MEDIE: top 100 ---")
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    stocks = load_exchange(ex)
    with_price = get_tickers_with_prices(ex)
    eligible = sorted(
        [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
        key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:100]
    no_price = [s["ticker"] for s in eligible if s["ticker"] not in with_price]
    print(f"{ex:<8} eligible={len(eligible):>5} con_prezzo={len(eligible)-len(no_price):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price[:30]}")

print()

# EU piccole — tutti
print("--- BORSE PICCOLE: tutti ---")
for ex in ["VI","IR","LS"]:
    stocks = load_exchange(ex)
    with_price = get_tickers_with_prices(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    no_price = [s["ticker"] for s in eligible if s["ticker"] not in with_price]
    print(f"{ex:<8} eligible={len(eligible):>5} con_prezzo={len(eligible)-len(no_price):>5} senza_prezzo={len(no_price):>4}")
    if no_price:
        print(f"         SENZA PREZZO: {no_price[:30]}")

print()

# US — top 2000
print("--- US: top 2000 ---")
stocks = load_exchange("US")
with_price = get_tickers_with_prices("US")
print(f"  Ticker US con prezzi recenti: {len(with_price)}")
eligible = sorted(
    [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
    key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:2000]
no_price = [s["ticker"] for s in eligible if s["ticker"] not in with_price]
print(f"US       eligible={len(eligible):>5} con_prezzo={len(eligible)-len(no_price):>5} senza_prezzo={len(no_price):>4}")
if no_price:
    print(f"         SENZA PREZZO: {no_price[:50]}")

print()

# TSX — top 400
print("--- TSX: top 400 ---")
stocks = load_exchange("TSX")
with_price = get_tickers_with_prices("TSX")
print(f"  Ticker TSX con prezzi recenti: {len(with_price)}")
eligible = sorted(
    [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))],
    key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:400]
no_price = [s["ticker"] for s in eligible if s["ticker"] not in with_price]
print(f"TSX      eligible={len(eligible):>5} con_prezzo={len(eligible)-len(no_price):>5} senza_prezzo={len(no_price):>4}")
if no_price:
    print(f"         SENZA PREZZO: {no_price[:50]}")

print()
print("=== NESSUNA MODIFICA AL DB ===")
