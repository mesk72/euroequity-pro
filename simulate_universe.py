import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

print("=== SIMULAZIONE NUOVO UNIVERSO ===")
print()

total_eu = 0

# EU — mkt_cap >= 500M (escludi ETF/fondi)
print("--- BORSE GRANDI: mkt_cap >= $500M ---")
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible={len(eligible):>5} oggi_in_universe={currently_in:>5}")
    total_eu += len(eligible)

print()

# EU — top 100 (escludi ETF/fondi)
print("--- BORSE MEDIE: top 100 per mkt_cap ---")
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    top100 = sorted(eligible, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:100]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible={len(top100):>5} oggi_in_universe={currently_in:>5}")
    total_eu += len(top100)

print()

# EU — tutti (escludi ETF/fondi)
print("--- BORSE PICCOLE: tutti ---")
for ex in ["VI","IR","LS"]:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible={len(eligible):>5} oggi_in_universe={currently_in:>5}")
    total_eu += len(eligible)

print()
print(f"TOTALE EU NUOVO UNIVERSO: {total_eu}")
print()

# NA
print("--- NORD AMERICA ---")
stocks_us = load_exchange("US")
eligible_us = [s for s in stocks_us if not is_excluded(s.get("company",""), s.get("sector",""))]
top2000 = sorted(eligible_us, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:2000]
currently_us = sum(1 for s in stocks_us if s.get("in_universe"))
print(f"US       totale={len(stocks_us):>5} eligible={len(top2000):>5} oggi_in_universe={currently_us:>5}")

stocks_tsx = load_exchange("TSX")
eligible_tsx = [s for s in stocks_tsx if not is_excluded(s.get("company",""), s.get("sector",""))]
top400 = sorted(eligible_tsx, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:400]
currently_tsx = sum(1 for s in stocks_tsx if s.get("in_universe"))
print(f"TSX      totale={len(stocks_tsx):>5} eligible={len(top400):>5} oggi_in_universe={currently_tsx:>5}")

print()
print(f"TOTALE NA NUOVO UNIVERSO: {len(top2000) + len(top400)}")
print()
print("=== NESSUNA MODIFICA FATTA — solo simulazione ===")
