import os, requests, csv, io, math
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

MIN_PRICE_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

EX_MAP = {"LSE":"LSE","AIM":"AIM"}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES GOLD","ISHARES SILVER","ISHARES PHYSICAL",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI","ISHARES MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
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

print("=== TEST UNIVERSO LSE (UK) ===")
print()

# Carica titoli LSE esistenti nel DB
stocks_db = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,company,in_universe",
                "exchange":"eq.LSE","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch: stocks_db[s["ticker"]] = s
    offset += 1000
    if len(batch)<1000: break

print(f"Titoli LSE nel DB: {len(stocks_db)}")
print(f"Attualmente in_universe: {sum(1 for s in stocks_db.values() if s.get('in_universe'))}")

# Carica TIKR EU e filtra LSE
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
tikr_lse = {}
for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    if ex_raw != "LSE": continue
    company = row.get("Company Name","").strip()
    mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
    tikr_lse[ticker] = {"company":company,"mkt_cap":mktcap}

print(f"Titoli LSE nel TIKR: {len(tikr_lse)}")

# Calcola eligible >= 400M
eligible = []
excluded = []
no_cap = []
for t, info in tikr_lse.items():
    mc = info["mkt_cap"] or 0
    if is_excluded(info["company"]):
        excluded.append((t, info["company"]))
    elif mc < 400:
        no_cap.append((t, mc))
    else:
        eligible.append((t, mc, info["company"]))

eligible.sort(key=lambda x: x[1], reverse=True)
new_tickers = [t for t,mc,c in eligible if t not in stocks_db]

print(f"\nEligible (>= 400M, non esclusi): {len(eligible)}")
print(f"Esclusi come ETF/fondi: {len(excluded)}")
print(f"Sotto 400M di mktcap: {len(no_cap)}")
print(f"Nuovi da inserire nel DB: {len(new_tickers)}")

# Verifica prezzi bulk
tickers_with_price = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":"eq.LSE",
                "date":f"gte.{MIN_PRICE_DATE}",
                "order":"ticker.asc","limit":"2000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for row in batch: tickers_with_price.add(row["ticker"])
    offset += 2000
    if len(batch)<2000: break

con_prezzi   = [(t,mc,c) for t,mc,c in eligible if t in tickers_with_price]
senza_prezzi = [(t,mc,c) for t,mc,c in eligible if t not in tickers_with_price]

print(f"\n=== VERIFICA PREZZI ===")
print(f"Con prezzi aggiornati: {len(con_prezzi)}")
print(f"Senza prezzi: {len(senza_prezzi)}")

if senza_prezzi:
    print("\nSenza prezzi:")
    for t,mc,c in senza_prezzi[:30]:
        print(f"  {t:<12} mktcap={mc:>8.0f} | {c}")
    if len(senza_prezzi) > 30:
        print(f"  ... e altri {len(senza_prezzi)-30}")

print(f"\n=== RIEPILOGO LSE ===")
print(f"  Nel TIKR:       {len(tikr_lse)}")
print(f"  Eligible:       {len(eligible)}")
print(f"  Con prezzi:     {len(con_prezzi)}")
print(f"  Senza prezzi:   {len(senza_prezzi)}")
print(f"  Nuovi da DB:    {len(new_tickers)}")

if excluded:
    print(f"\nEsclusi ({len(excluded)}):")
    for t,c in excluded[:20]:
        print(f"  {t:<12} {c}")
