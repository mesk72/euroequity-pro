import os, requests, csv, io, math
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "return=minimal"}

MIN_PRICE_DATE = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","SWX":"SWX","LSE":"LSE","CPSE":"CPSE",
    "HMSE":"OM","XSAT":"OM","OB":"OB","OTCNO":"OB",
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "ARCA":"US","OTCPK":"US","NYSEAM":"US",
    "TSX":"TSX","TSXV":"TSX","CNSX":"TSX","NEOE":"TSX",
}

COUNTRY_FLAG = {
    "ITA":"🇮🇹","USA":"🇺🇸","CAN":"🇨🇦","GBR":"🇬🇧","DEU":"🇩🇪",
    "FRA":"🇫🇷","SWE":"🇸🇪","CHE":"🇨🇭","NLD":"🇳🇱","BEL":"🇧🇪",
    "ESP":"🇪🇸","FIN":"🇫🇮","DNK":"🇩🇰","NOR":"🇳🇴","AUT":"🇦🇹",
    "IRL":"🇮🇪","PRT":"🇵🇹",
}
CURRENCY_MAP = {
    "MIL":"EUR","XETRA":"EUR","PA":"EUR","LSE":"GBP","OM":"SEK",
    "SWX":"CHF","OB":"NOK","AS":"EUR","MC":"EUR","BR":"EUR",
    "HE":"EUR","CPSE":"DKK","VI":"EUR","IR":"EUR","LS":"EUR",
    "US":"USD","TSX":"CAD",
}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES GOLD","ISHARES SILVER",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
]

def is_excluded(company):
    name = (company or "").upper()
    return any(kw in name for kw in ALWAYS_EXCLUDE)

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

# TEST SOLO SU MIL
print("=== TEST UNIVERSO MILANO ===")
print()

# 1. Carica titoli MIL esistenti
stocks_mil = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,company,in_universe",
                "exchange":"eq.MIL","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch: stocks_mil[s["ticker"]] = s
    offset += 1000
    if len(batch)<1000: break
print(f"Titoli MIL nel DB: {len(stocks_mil)}")
print(f"Attualmente in_universe: {sum(1 for s in stocks_mil.values() if s.get('in_universe'))}")

# 2. Carica TIKR EU e filtra MIL
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
tikr_mil = {}
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, ex_raw)
    if exchange != "MIL": continue
    company = row.get("Company Name","").strip()
    mktcap = parse_mktcap(row.get("Last Mkt Cap",""))
    tikr_mil[ticker] = {"company":company,"mkt_cap":mktcap,"ex_raw":ex_raw}

print(f"Titoli MIL nel TIKR: {len(tikr_mil)}")

# 3. Nuovi titoli da inserire
new_tickers = [t for t in tikr_mil if t not in stocks_mil]
print(f"Nuovi titoli da inserire: {len(new_tickers)}")
for t in new_tickers:
    print(f"  {t} | {tikr_mil[t]['company']} | mktcap={tikr_mil[t]['mkt_cap']}")

# 4. Calcola eligible (mkt_cap >= 400M, non esclusi)
mktcap_tikr = {t: tikr_mil[t]["mkt_cap"] or 0 for t in tikr_mil}
eligible = []
excluded = []
no_cap = []
for t, info in tikr_mil.items():
    mc = info["mkt_cap"] or 0
    if is_excluded(info["company"]):
        excluded.append(t)
    elif mc < 400:
        no_cap.append((t, mc, info["company"]))
    else:
        eligible.append((t, mc, info["company"]))

eligible.sort(key=lambda x: x[1], reverse=True)
print(f"\nEligible (>= 400M, non esclusi): {len(eligible)}")
print(f"Esclusi come ETF/fondi: {len(excluded)}")
print(f"Sotto 400M: {len(no_cap)}")
print()
print("Titoli eligible MIL:")
for t, mc, c in eligible:
    in_db = "IN DB" if t in stocks_mil else "NUOVO"
    print(f"  {t:<15} mktcap={mc:>10.0f} | {c} [{in_db}]")
