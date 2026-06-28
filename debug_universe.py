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

EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]
EXCLUDE_EXACT = [
    "UCITS","XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","WISDOMTREE ETF","VANECK ETF","INDEX FUND",
    "BOND FUND","EXCHANGE TRADED","EXCHANGE-TRADED",
]
PASSIVE_KEYWORDS = ["ETF","ETP","ETC","UCITS","INDEX","TRACKER","SHARES TRUST"]
ASSET_MANAGERS = ["BLACKROCK","INVESCO","WISDOMTREE","ISHARES","VANECK","SPDR","VANGUARD"]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()
    for kw in EXCLUDE_EXACT:
        if kw in name: return True
    if " FUND" in name:
        if any(x in name for x in ["REALTY","REIT","PROPERTY","PROPERTIES",
                                    "INFRASTRUCTURE","INCOME TRUST","ROYALTY"]):
            pass
        else:
            return True
    for am in ASSET_MANAGERS:
        if am in name:
            if any(p in name for p in ["ETF","ETP","ETC","FUND","NOTES","SHARES","INDEX","MINI"]):
                return True
    if "NOTES" in name and any(x in name for x in ["LEVERAGED","3X","2X","-1X","ETNS","DUE "]):
        return True
    return False

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

excluded = []
included_check = ["NFLX","BLK","IVZ","WT","AMT","PLD","EQIX","WELL","VTR","SPG"]
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, None)
    company = row.get("Company Name","").strip()
    sector = row.get("Sector","").strip()
    if exchange not in ("US","TSX"): continue
    excl = is_excluded(company, sector)
    if excl:
        excluded.append((ticker, company))
    if ticker in included_check:
        print(f"  CHECK {ticker}: {'ESCLUSO ❌' if excl else 'INCLUSO ✅'} | {company}")

print(f"\nTotale esclusi: {len(excluded)}")
print("\nLista esclusi:")
for t, c in sorted(excluded):
    print(f"  {t:<12} {c}")
