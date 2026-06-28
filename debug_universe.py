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

# Parole che identificano SEMPRE un prodotto passivo/fondo da escludere
ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS","XTRACKERS","LYXOR",
    "INDEX FUND","BOND FUND","EXCHANGE TRADED NOTE",
    "EXCHANGE-TRADED NOTE","LEVERAGED NOTE",
    "GOLD SHARES","SILVER TRUST","GOLD TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER",
    "COVERED CALL","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","URANIUM TRUST FUND",
    "COMMODITY INDEX","AGRICULTURE FUND",
    "HIGH INTEREST SAVINGS","CASH FUND","CASH MANAGEMENT FUND",
    "DYNAMIC OVERWRITE FUND","PREMIUM YIELD FUND",
    "MARKET NEUTRAL","LONG SHORT INCOME",
    "GROWTH TECH FUND","PRIVATE REAL ESTATE FUND",
    "GLOBAL EQUITY+ FUND","ENERGY FUND",
    "NEXT GENERATION CONNECTIVITY FUND",
    "DIVIDEND, INTEREST & PREMIUM","TOTAL RETURN FUND",
    "STRATEGIC INVESTMENT FUND","STRATEGIC TOTAL RETURN FUND",
    "INFRASTRUCTURE FUND","INCOME SOLUTIONS FUND",
    "ENERGY INFRASTRUCTURE FUND",
    "3X LEVERAGED","2X LEVERAGED","-1X",
    "MINIATURES","MINI SHARES",
    "MULTISECTOR COMMODITY",
]

# Fondi con prefisso gestore — escludi SOLO se accompagnati da FUND/ETF/NOTES
MANAGER_PRODUCTS = {
    "ISHARES": ["ETF","ETP","ETC","TRUST","FUND","SHARES","PHYSICAL","MINI"],
    "BLACKROCK": ["ETF","ETP","ETC","FUND","NOTES","TRUST TERM","TERM TRUST",
                  "TAXABLE MUNICIPAL","CREDIT ALLOCATION","ESG CAPITAL","HEALTH SCIENCES",
                  "INNOVATION AND GROWTH","SCIENCE AND TECHNOLOGY","MUNICIPAL 2030",
                  "ENHANCED EQUITY","CAPITAL ALLOCATION TERM"],
    "INVESCO DB": ["FUND","COMMODITY","AGRICULTURE"],
    "VANGUARD": ["ETF","FUND","INDEX"],
    "SPDR": ["ETF","FUND","SHARES","MINISHARES"],
    "WISDOMTREE": ["ETF","FUND"],
    "VANECK": ["ETF","FUND"],
    "NUVEEN": ["FUND","OVERWRITE"],
    "BMO": ["FUND","ETF","COVERED CALL"],
    "PURPOSE": ["FUND","CASH","SAVINGS"],
    "SPROTT PHYSICAL": ["FUND","TRUST FUND"],
    "CORNERSTONE": ["FUND","INVESTMENT FUND","TOTAL RETURN FUND"],
    "NEUBERGER BERMAN": ["FUND","INC."],
    "CALAMOS": ["FUND"],
    "COHEN & STEERS": ["FUND"],
    "DOUBLELINE": ["FUND"],
    "KAYNE ANDERSON": ["FUND"],
    "VIRTUS": ["FUND"],
    "PICTON": ["FUND"],
    "FIDELITY GLOBAL": ["FUND"],
    "NINEPOINT": ["FUND"],
    "CI GLOBAL": ["FUND"],
    "SRH TOTAL": ["FUND"],
    "FUNDRISE": ["FUND"],
    "MICORSECTORS": ["NOTE"],
    "MICROSECTORS": ["NOTE"],
}

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()

    # Check sempre esclusi
    for kw in ALWAYS_EXCLUDE:
        if kw in name: return True

    # Check manager + prodotto
    for manager, products in MANAGER_PRODUCTS.items():
        if manager in name:
            if any(p in name for p in products):
                return True

    return False

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

excluded = []
check_list = ["NFLX","BLK","IVZ","WT","AMT","PLD","EQIX","WELL","VTR","SPG",
              "VICI","DLR","EQR","AVB","EXR","ESS","ARE","SBAC","CCI","O",
              "PSA","IRM","REG","KIM","FRT","HST","ADC","STAG","COLD","LINE"]
included_ok = []
excluded_bad = []

rows_all = []
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
        if excl:
            excluded_bad.append(f"  {ticker}: ESCLUSO ❌ | {company}")
        else:
            included_ok.append(f"  {ticker}: INCLUSO ✅ | {company}")

print("=== CHECK TITOLI CHIAVE ===")
for x in sorted(included_ok): print(x)
for x in sorted(excluded_bad): print(x)
print(f"\nTotale esclusi: {len(excluded)}")
print("\nLista esclusi:")
for t, c in sorted(excluded):
    print(f"  {t:<12} {c}")
