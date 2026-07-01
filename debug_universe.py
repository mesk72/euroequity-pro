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

# Settori da escludere — SOLO quelli puramente passivi
# NON includere Real Estate (71-77) perché REIT sono investibili
EXCLUDE_SECTORS = []  # nessun settore escluso per ora

# Esclusioni per nome — solo prodotti passivi certi
ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "DYNAMIC OVERWRITE FUND","PREMIUM YIELD FUND",
    "COMMODITY INDEX TRACKING","AGRICULTURE FUND",
    "HIGH INTEREST SAVINGS",
    "3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","SPDR SILVER",
    "ISHARES GOLD","ISHARES SILVER","ISHARES PHYSICAL",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MARKET NEUTRAL EQUITY","LONG SHORT INCOME",
    "GROWTH TECH FUND","PRIVATE REAL ESTATE FUND",
    "GLOBAL EQUITY+ FUND","NINEPOINT ENERGY FUND",
    "CI GLOBAL ARTIFICIAL INTELLIGENCE FUND",
    "INCOME SOLUTIONS FUND","ENERGY INFRASTRUCTURE FUND",
    "OVERWRITE FUND","URANIUM TRUST FUND",
    "MULTISECTOR COMMODITY","INVESCO DB ",
    "MICROSECTORS","BMO COVERED CALL","BMO MONEY MARKET",
    "BMO PREMIUM YIELD","PURPOSE CASH","PURPOSE HIGH INTEREST",
    "SPROTT PHYSICAL URANIUM","PICTON LONG SHORT",
    "PICTON MARKET NEUTRAL","FIDELITY GLOBAL EQUITY+",
    "SRH TOTAL RETURN FUND","FUNDRISE GROWTH",
    "CORNERSTONE STRATEGIC INVESTMENT FUND",
    "CORNERSTONE TOTAL RETURN FUND","CALAMOS STRATEGIC",
    "COHEN & STEERS QUALITY INCOME REALTY FUND",
    "COHEN & STEERS INFRASTRUCTURE FUND",
    "DOUBLELINE INCOME SOLUTIONS","KAYNE ANDERSON ENERGY",
    "VIRTUS DIVIDEND, INTEREST","NEUBERGER BERMAN NEXT GENERATION",
    "NUVEEN NASDAQ","NUVEEN S&P","BLUEROCK PRIVATE",
    "CIM REAL ESTATE FINANCE TRUST",
    "MUTUAL FUND","MUTUALFUND",
]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()
    for kw in ALWAYS_EXCLUDE:
        if kw in name: return True
    return False

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

excluded = []
check_list = [
    "NFLX","BLK","IVZ","WT","AMT","PLD","EQIX","WELL","VTR","SPG",
    "VICI","DLR","EQR","AVB","EXR","ESS","ARE","SBAC","CCI","O",
    "PSA","IRM","REG","KIM","FRT","HST","ADC","STAG","COLD","LINE",
    "CPT","SUI","UDR","INVH","CUBE","SAFE","NSA","WY","GLPI",
]

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
    if ticker in check_list:
        print(f"  {ticker:<8} {'ESCLUSO ❌' if excl else 'INCLUSO ✅'} | {company}")

print(f"\nTotale esclusi: {len(excluded)}")
print("\nLista esclusi:")
for t, c in sorted(excluded):
    print(f"  {t:<12} {c}")
