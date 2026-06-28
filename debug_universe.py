import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EXCLUDE_NAMES = [
    "ETF","FUND","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]
EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    return any(kw in (company or "").upper() for kw in EXCLUDE_NAMES)

EX_MAP = {
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "TSX":"TSX","TSXV":"TSX",
}

# 1. Carica tutti i titoli US dal DB
print("=== US NEL DB ===")
stocks_db = {}
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,company,sector","exchange":"eq.US",
                "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for s in batch: stocks_db[s["ticker"]] = s
    offset += 1000
    if len(batch)<1000: break

excluded_db = {t:s for t,s in stocks_db.items() if is_excluded(s.get("company",""),s.get("sector",""))}
print(f"  Totale US nel DB: {len(stocks_db)}")
print(f"  Esclusi come ETF/fondi: {len(excluded_db)}")
print(f"  Eligible nel DB: {len(stocks_db)-len(excluded_db)}")
print(f"  Esempi esclusi: {list(excluded_db.keys())[:20]}")

# 2. Carica TIKR NA
print("\n=== TIKR NA ===")
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
tikr_us = {}
tikr_tsx = {}
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, ex_raw)
    company = row.get("Company Name","").strip()
    sector = row.get("Sector","").strip()
    if exchange == "US": tikr_us[ticker] = {"company":company,"sector":sector,"ex_raw":ex_raw}
    elif exchange == "TSX": tikr_tsx[ticker] = {"company":company,"sector":sector}

print(f"  US nel TIKR: {len(tikr_us)}")
print(f"  TSX nel TIKR: {len(tikr_tsx)}")

# 3. Confronto
in_tikr_not_db = [t for t in tikr_us if t not in stocks_db]
in_db_not_tikr = [t for t in stocks_db if t not in tikr_us]
esclusi_tikr = [t for t,s in tikr_us.items() if is_excluded(s["company"],s["sector"])]

print(f"\n=== CONFRONTO ===")
print(f"  Nel TIKR ma NON nel DB: {len(in_tikr_not_db)}")
print(f"  Nel DB ma NON nel TIKR: {len(in_db_not_tikr)}")
print(f"  Esclusi come ETF/fondi nel TIKR: {len(esclusi_tikr)}")
print(f"  Esempi TIKR non nel DB: {in_tikr_not_db[:20]}")
print(f"  Esempi esclusi TIKR: {esclusi_tikr[:20]}")

# Exchange raw non mappati
ex_raw_unknown = set()
for row_data in tikr_us.values():
    ex = row_data.get("ex_raw","")
    if ex not in EX_MAP:
        ex_raw_unknown.add(ex)
print(f"\n  Exchange raw non mappati: {ex_raw_unknown}")
