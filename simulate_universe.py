import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Settori da escludere (ETF, fondi, veicoli finanziari passivi)
EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]

# Parole chiave da escludere nel nome società
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

def load_exchange(exchange, limit=5000):
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

total_new = 0

# EU — mkt_cap >= 500M
EU_500M = ["LSE","XETRA","PA","OM","SWX","MIL"]
for ex in EU_500M:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible(>500M)={len(eligible):>5} attuale_in_universe={currently_in:>5}")
    total_new += len(eligible)

print()

# EU — top 100
EU_TOP100 = ["AS","MC","BR","HE","CPSE","OB","NGM"]
for ex in EU_TOP100:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    eligible_sorted = sorted(eligible, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:100]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible(top100)={len(eligible_sorted):>5} attuale_in_universe={currently_in:>5}")
    total_new += len(eligible_sorted)

print()

# EU — tutti
EU_ALL = ["VI","IR","LS","AIM","AT","GR"]
for ex in EU_ALL:
    stocks = load_exchange(ex)
    eligible = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    currently_in = sum(1 for s in stocks if s.get("in_universe"))
    print(f"{ex:<8} totale={len(stocks):>5} eligible(tutti)={len(eligible):>5} attuale_in_universe={currently_in:>5}")
    total_new += len(eligible)

print()
print(f"TOTALE EU NUOVO UNIVERSO: {total_new}")
print()

# US — top 2000
stocks_us = load_exchange("US")
eligible_us = [s for s in stocks_us if not is_excluded(s.get("company",""), s.get("sector",""))]
eligible_us_sorted = sorted(eligible_us, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:2000]
currently_us = sum(1 for s in stocks_us if s.get("in_universe"))
print(f"US       totale={len(stocks_us):>5} eligible(top2000)={len(eligible_us_sorted):>5} attuale_in_universe={currently_us:>5}")

# TSX — top 400
stocks_tsx = load_exchange("TSX")
eligible_tsx = [s for s in stocks_tsx if not is_excluded(s.get("company",""), s.get("sector",""))]
eligible_tsx_sorted = sorted(eligible_tsx, key=lambda s: s.get("mkt_cap") or 0, reverse=True)[:400]
currently_tsx = sum(1 for s in stocks_tsx if s.get("in_universe"))
print(f"TSX      totale={len(stocks_tsx):>5} eligible(top400)={len(eligible_tsx_sorted):>5} attuale_in_universe={currently_tsx:>5}")

print()
print(f"TOTALE NA NUOVO UNIVERSO: {len(eligible_us_sorted) + len(eligible_tsx_sorted)}")
print()
print("=== NESSUNA MODIFICA FATTA — solo simulazione ===")
