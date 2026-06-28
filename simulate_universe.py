import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

TODAY = datetime.now().strftime("%Y-%m-%d")
MIN_PRICE_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]
EXCLUDE_NAMES = [
    "ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS:
        return True
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

def has_recent_price(ticker, exchange):
    """Verifica se il titolo ha un prezzo negli ultimi 10 giorni"""
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date", "ticker": f"eq.{ticker}",
                "exchange": f"eq.{exchange}",
                "date": f"gte.{MIN_PRICE_DATE}",
                "limit": "1"})
    rows = r.json()
    return isinstance(rows, list) and len(rows) > 0

def check_exchange(stocks, label):
    no_price = []
    for s in stocks:
        if not has_recent_price(s["ticker"], s["exchange"]):
            no_price.append(s["ticker"])
    ok = len(stocks) - len(no_price)
    print(f"  {label}: {len(stocks)} titoli — {ok} con prezzi OK — {len(no_price)} SENZA prezzi")
    if no_price:
        print(f"    Senza prezzi: {no_price[:20]}")
    return no_price

print("=== SIMULAZIONE + VERIFICA PREZZI ===")
print(f"Data riferimento prezzi: >= {MIN_PRICE_DATE}")
print()

UNIVERSE = {}

# EU grandi
print("--- BORSE GRANDI: mkt_cap >= $500M ---")
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex}: totale={len(stocks)} eligible={len(eligible)} oggi_in={currently_in}")
    no_price = check_exchange(eligible, ex)
    # Escludi senza prezzi dall universo finale
    UNIVERSE[ex] = [s for s in eligible if s["ticker"] not in no_price]

print()

# EU medie
print("--- BORSE MEDIE: top 100 ---")
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    top100 = sorted(eligible, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:100]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex}: totale={len(stocks)} eligible={len(top100)} oggi_in={currently_in}")
    no_price = check_exchange(top100, ex)
    UNIVERSE[ex] = [s for s in top100 if s["ticker"] not in no_price]

print()

# EU piccole
print("--- BORSE PICCOLE: tutti ---")
for ex in ["VI","IR","LS"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex}: totale={len(stocks)} eligible={len(eligible)} oggi_in={currently_in}")
    no_price = check_exchange(eligible, ex)
    UNIVERSE[ex] = [s for s in eligible if s["ticker"] not in no_price]

total_eu = sum(len(v) for v in UNIVERSE.values())
print()
print(f"TOTALE EU CON PREZZI: {total_eu}")
print()

# NA
print("--- NORD AMERICA ---")
stocks_us = load_exchange("US")
eligible_us = [s for s in stocks_us if not is_excluded(s.get("company",""), s.get("sector",""))]
top2000 = sorted(eligible_us, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:2000]
currently_us = sum(1 for s in stocks_us if s.get("in_universe"))
print(f"US: totale={len(stocks_us)} eligible={len(top2000)} oggi_in={currently_us}")
no_price_us = check_exchange(top2000, "US")
UNIVERSE["US"] = [s for s in top2000 if s["ticker"] not in no_price_us]

stocks_tsx = load_exchange("TSX")
eligible_tsx = [s for s in stocks_tsx if not is_excluded(s.get("company",""), s.get("sector",""))]
top400 = sorted(eligible_tsx, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:400]
currently_tsx = sum(1 for s in stocks_tsx if s.get("in_universe"))
print(f"TSX: totale={len(stocks_tsx)} eligible={len(top400)} oggi_in={currently_tsx}")
no_price_tsx = check_exchange(top400, "TSX")
UNIVERSE["TSX"] = [s for s in top400 if s["ticker"] not in no_price_tsx]

total_na = len(UNIVERSE["US"]) + len(UNIVERSE["TSX"])
print()
print(f"TOTALE NA CON PREZZI: {total_na}")
print()
print(f"TOTALE GLOBALE EU+NA CON PREZZI: {total_eu + total_na}")
print()
print("=== NESSUNA MODIFICA FATTA — solo simulazione ===")
