import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

TIKR_FY_EXCHANGE_MAP = {
    "NasdaqGS": "US", "NasdaqGM": "US", "NasdaqCM": "US",
    "NYSE": "US", "NYSEAM": "US", "ARCA": "US", "BATS": "US",
    "OTCPK": "US", "CNSX": "US",
    "JPX": "TSE", "HKEX": "SEHK", "KOSDAQ": "KRX",
    "TSXV": "TSX",
    "Catalist": "SGX",
}
def norm(raw): return TIKR_FY_EXCHANGE_MAP.get(raw, raw)

# 1. Ticker US dal nuovo file TIKR (stessa normalizzazione)
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
us_tickers = set()
ca_tickers = set()
for row in reader:
    ex = row.get("Primary Exchange","").strip()
    t = row.get("Ticker","").strip()
    if not t: continue
    if norm(ex) == "US": us_tickers.add(t)
    elif norm(ex) == "TSX": ca_tickers.add(t)
print(f"Ticker US nel nuovo file TIKR (normalizzati): {len(us_tickers)}")
print(f"Ticker TSX/Canada nel nuovo file TIKR (normalizzati): {len(ca_tickers)}")

# 2. Copertura fiscal_year_end.csv per US (con la STESSA normalizzazione)
rf = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
readerf = csv.DictReader(io.StringIO(rf.text))
fy_us = set()
for row in readerf:
    if norm(row.get("exchange","").strip()) == "US":
        fy_us.add(row.get("ticker","").strip())
print(f"Copertura fiscal_year_end.csv per US (normalizzata): {len(fy_us)}")

missing = us_tickers - fy_us
print(f"MANCANTI: {len(missing)}")
print(f"Esempio 15: {list(missing)[:15]}")
