import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EX_MAP = {
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "ARCA":"US","OTCPK":"US","NYSEAM":"US",
    "TSX":"TSX","TSXV":"TSX","CNSX":"TSX","NEOE":"TSX",
}

# Logica esclusione attuale
EXCLUDE_NAMES = [
    "ETF","FUND","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]
EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]

def is_excluded_current(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    return any(kw in (company or "").upper() for kw in EXCLUDE_NAMES)

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

excluded = []
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, None)
    company = row.get("Company Name","").strip()
    sector = row.get("Sector","").strip()
    if exchange not in ("US","TSX"): continue
    if is_excluded_current(company, sector):
        # Trova quale keyword lo esclude
        matched = [kw for kw in EXCLUDE_NAMES if kw in company.upper()]
        excluded.append((ticker, exchange, company, sector, matched))

print(f"Totale esclusi US+TSX: {len(excluded)}")
print()
for ticker, exchange, company, sector, matched in sorted(excluded):
    print(f"  {ticker:<10} {exchange:<5} matched={matched} | {company}")
