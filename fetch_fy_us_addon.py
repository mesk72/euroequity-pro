import os, requests, csv, io, time
from datetime import datetime, timezone

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance")

TIKR_FY_EXCHANGE_MAP = {
    "NasdaqGS": "US", "NasdaqGM": "US", "NasdaqCM": "US",
    "NYSE": "US", "NYSEAM": "US", "ARCA": "US", "BATS": "US",
    "OTCPK": "US", "CNSX": "US",
    "JPX": "TSE", "HKEX": "SEHK", "KOSDAQ": "KRX",
    "TSXV": "TSX",
    "Catalist": "SGX",
}
def norm(raw): return TIKR_FY_EXCHANGE_MAP.get(raw, raw)

print("=" * 60)
print("[1/3] Ticker US dal nuovo TIKR + copertura FY esistente")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
us_tickers = set()
for row in reader:
    ex = row.get("Primary Exchange","").strip()
    t = row.get("Ticker","").strip()
    if t and norm(ex) == "US": us_tickers.add(t)
print(f"  Ticker US nel file TIKR: {len(us_tickers)}")

rf = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
readerf = csv.DictReader(io.StringIO(rf.text))
fy_us = set()
for row in readerf:
    if norm(row.get("exchange","").strip()) == "US":
        fy_us.add(row.get("ticker","").strip())
print(f"  Gia' coperti in fiscal_year_end.csv: {len(fy_us)}")

missing = sorted(us_tickers - fy_us)
print(f"  MANCANTI da recuperare da Yahoo: {len(missing)}")

print()
print("=" * 60)
print("[2/3] Download fiscal year end da Yahoo (yfinance)")
print("=" * 60)
results = []
not_found = []
for i, ticker in enumerate(missing):
    try:
        info = yf.Ticker(ticker).info
        ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
        if ts:
            month = datetime.fromtimestamp(ts, tz=timezone.utc).month
            results.append({"ticker": ticker, "exchange": "US", "fiscal_month": month})
        else:
            not_found.append(ticker)
    except Exception as e:
        not_found.append(ticker)
    if (i+1) % 50 == 0:
        print(f"  ...{i+1}/{len(missing)} processati ({len(results)} trovati, {len(not_found)} falliti)")
    time.sleep(0.15)

print(f"\n  Trovati: {len(results)}")
print(f"  Non trovati (default dicembre nel sistema): {len(not_found)}")
if not_found:
    print(f"  Esempio non trovati: {not_found[:20]}")

print()
print("=" * 60)
print("[3/3] Scrittura CSV")
print("=" * 60)
out_path = "fiscal_year_end_us_addon.csv"
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","fiscal_month"])
    w.writeheader()
    for row in results:
        w.writerow(row)
print(f"  Scritto {out_path} con {len(results)} righe")
print("\nFATTO.")
