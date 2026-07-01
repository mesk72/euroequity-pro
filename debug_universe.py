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

# Parole che indicano una società INVESTIBILE — se presenti nel nome
# il titolo non va escluso anche se ha altre keyword sospette
INVESTIBLE_SIGNALS = [
    "REIT","REAL ESTATE INVESTMENT TRUST","INVESTMENT TRUST",
    "REALTY","PROPERTIES","PROPERTY GROUP","PROPERTY TRUST",
    "REALTY TRUST","REALTY CORP","REALTY CO",
    "HOSPITALITY","HEALTHCARE REIT","INDUSTRIAL REIT",
    "APARTMENT REIT","RESIDENTIAL REIT","INDUSTRIAL TRUST",
    "INFRASTRUCTURE TRUST","GROCERY REIT","RETAIL REIT",
    " INC."," INC,"," CORP."," CORP,"," LTD."," LTD,",
    " PLC"," LLC"," LP ","L.P.","S.P.A.","N.V.","S.A.",
    "INCORPORATED","CORPORATION","COMPANY",
]

# Parole che identificano SEMPRE un prodotto passivo da escludere
# Anche se c'è un segnale investibile
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
]

# Fondi specifici da escludere per nome gestore + tipo prodotto
# MA solo se NON hanno segnali investibili
PASSIVE_PATTERNS = [
    ("XTRACKERS",),("LYXOR",),("VANGUARD ETF",),("AMUNDI ETF",),
    ("SPDR ETF",),("SPDR GOLD",),("SPDR SILVER",),
    ("ISHARES GOLD",),("ISHARES SILVER",),("ISHARES PHYSICAL",),
    ("WISDOMTREE ETF",),("VANECK ETF",),
    ("INDEX FUND",),("BOND FUND",),
    ("MARKET NEUTRAL",),("LONG SHORT INCOME",),
    ("GROWTH TECH FUND",),("PRIVATE REAL ESTATE FUND",),
    ("GLOBAL EQUITY+ FUND",),("ENERGY FUND",),
    ("CONNECTIVITY FUND",),("INFRASTRUCTURE FUND",),
    ("INCOME SOLUTIONS FUND",),("ENERGY INFRASTRUCTURE FUND",),
    ("OVERWRITE FUND",),("URANIUM TRUST FUND",),
    ("MULTISECTOR COMMODITY",),("INVESCO DB ",),
    ("MICROSECTORS",),("MICORSECTORS",),
    ("BMO COVERED CALL",),("BMO MONEY MARKET",),("BMO PREMIUM YIELD",),
    ("PURPOSE CASH",),("PURPOSE FUND",),("PURPOSE US CASH",),
    ("PURPOSE HIGH INTEREST",),("SPROTT PHYSICAL URANIUM",),
    ("PICTON LONG SHORT",),("PICTON MARKET NEUTRAL",),
    ("FIDELITY GLOBAL EQUITY+",),("NINEPOINT ENERGY",),
    ("CI GLOBAL ARTIFICIAL",),("SRH TOTAL RETURN FUND",),
    ("FUNDRISE GROWTH",),("CORNERSTONE STRATEGIC INVESTMENT FUND",),
    ("CORNERSTONE TOTAL RETURN FUND",),("CALAMOS STRATEGIC",),
    ("COHEN & STEERS QUALITY INCOME REALTY FUND",),
    ("COHEN & STEERS INFRASTRUCTURE FUND",),
    ("DOUBLELINE INCOME SOLUTIONS",),("KAYNE ANDERSON ENERGY",),
    ("VIRTUS DIVIDEND",),("NEUBERGER BERMAN NEXT GENERATION",),
    ("NUVEEN NASDAQ",),("NUVEEN S&P",),
    ("BLUEROCK PRIVATE",),("CIM REAL ESTATE FINANCE TRUST",),
    ("SRH TOTAL RETURN",),("FUNDRISE",),
]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()

    # Prima controlla se è un segnale investibile
    is_investible = any(s in name for s in INVESTIBLE_SIGNALS)

    # Sempre escludi indipendentemente
    for kw in ALWAYS_EXCLUDE:
        if kw in name: return True

    # Escludi per pattern passivi
    for pattern in PASSIVE_PATTERNS:
        if all(p in name for p in pattern):
            # Ma non se ha segnale investibile forte
            if is_investible and any(s in name for s in [
                "REIT","REAL ESTATE INVESTMENT TRUST","REALTY CORP",
                "REALTY TRUST","PROPERTY TRUST","PROPERTIES INC"
            ]):
                continue
            return True

    return False

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

excluded = []
check_list = [
    "NFLX","BLK","IVZ","WT","AMT","PLD","EQIX","WELL","VTR","SPG",
    "VICI","DLR","EQR","AVB","EXR","ESS","ARE","SBAC","CCI","O",
    "PSA","IRM","REG","KIM","FRT","HST","ADC","STAG","COLD","LINE",
    "BXDC","CPT","MPT","SUI","UDR","INVH","CUBE","SAFE","NSA",
    "WY","RYN","GLPI","OUT","LAMR","SVC","DHC",
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
        status = "ESCLUSO ❌" if excl else "INCLUSO ✅"
        print(f"  {ticker:<8} {status} | {company}")

print(f"\nTotale esclusi: {len(excluded)}")
print("\nLista esclusi:")
for t, c in sorted(excluded):
    print(f"  {t:<12} {c}")
