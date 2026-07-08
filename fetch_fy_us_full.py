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
print("[1/3] Ticker US dal file TIKR (tutti, non solo i mancanti)")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
us_tickers = set()
for row in reader:
    ex = row.get("Primary Exchange","").strip()
    t = row.get("Ticker","").strip()
    if t and norm(ex) == "US": us_tickers.add(t)
us_tickers = sorted(us_tickers)
print(f"  Ticker US totali: {len(us_tickers)}")

# Copertura gia' esistente in fiscal_year_end.csv — verra' comunque
# ri-scaricata da Yahoo per uniformita', ma la logghiamo per confronto
rf = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
readerf = csv.DictReader(io.StringIO(rf.text))
fy_us_existing = {}
for row in readerf:
    if norm(row.get("exchange","").strip()) == "US":
        fy_us_existing[row.get("ticker","").strip()] = row.get("fiscal_month","12")
print(f"  Gia' presenti nel file attuale: {len(fy_us_existing)}")

print()
print("=" * 60)
print("[2/3] Download fiscal year end da Yahoo per TUTTI i 3503")
print("=" * 60)
results = {}
not_found = []
t0 = time.time()
for i, ticker in enumerate(us_tickers):
    try:
        info = yf.Ticker(ticker).info
        ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
        if ts:
            month = datetime.fromtimestamp(ts, tz=timezone.utc).month
            results[ticker] = month
        else:
            not_found.append(ticker)
    except Exception:
        not_found.append(ticker)
    if (i + 1) % 100 == 0:
        elapsed = time.time() - t0
        print(f"  ...{i+1}/{len(us_tickers)} ({elapsed/60:.1f} min) — trovati={len(results)} falliti={len(not_found)}")
    time.sleep(0.15)

print(f"\n  Trovati su Yahoo: {len(results)}")
print(f"  Non trovati: {len(not_found)}")

# Per i non trovati, usa il valore gia' presente nel file esistente se c'e'
# (meglio di un default dicembre generico), altrimenti dicembre
recovered_from_existing = 0
for t in not_found:
    if t in fy_us_existing:
        recovered_from_existing += 1
print(f"  Di cui recuperabili dal file esistente: {recovered_from_existing}")
print(f"  Restano a default dicembre: {len(not_found) - recovered_from_existing}")

print()
print("=" * 60)
print("[3/3] Scrittura CSV unico — copre tutti i 3503 candidati US")
print("=" * 60)
out_path = "fiscal_year_end_us_full.csv"
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","fiscal_month"])
    w.writeheader()
    for t in us_tickers:
        if t in results:
            month = results[t]
        elif t in fy_us_existing:
            month = fy_us_existing[t]
        else:
            month = 12
        w.writerow({"ticker": t, "exchange": "US", "fiscal_month": month})
print(f"  Scritto {out_path} con {len(us_tickers)} righe (copertura 100% dei 3503 candidati)")
print("\nFATTO.")
