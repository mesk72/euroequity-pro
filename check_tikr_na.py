import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Metadata del file (data modifica)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/info/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
print("METADATA:", r.status_code, r.text[:300])

r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
rows = list(reader)
us_rows = [row for row in rows if row.get("Primary Exchange","").strip() in
           ("NYSE","NASDAQ","AMEX","OTC","PINK","NYSEARCA","BATS","")]
ca_rows = [row for row in rows if "TSX" in row.get("Primary Exchange","").strip().upper()
           or row.get("Primary Exchange","").strip() in ("TSX","TSXV")]
print(f"Righe totali file: {len(rows)}")
print(f"Righe US-like: {len(us_rows)}")
print(f"Righe TSX-like: {len(ca_rows)}")
print(f"Colonne disponibili: {list(rows[0].keys()) if rows else 'N/A'}")

# Fiscal year end coverage attuale per US
rf = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
readerf = csv.DictReader(io.StringIO(rf.text))
fy_us_tickers = set()
for row in readerf:
    if row.get("exchange","").strip() == "US":
        fy_us_tickers.add(row.get("ticker","").strip())
print(f"\nFiscal year end coverage attuale per US: {len(fy_us_tickers)} ticker")

us_tickers_tikr = set(row.get("Ticker","").strip() for row in us_rows)
missing = us_tickers_tikr - fy_us_tickers
print(f"Ticker US nel nuovo file TIKR: {len(us_tickers_tikr)}")
print(f"Di cui MANCANTI in fiscal_year_end.csv: {len(missing)}")
print(f"Esempio 10 mancanti: {list(missing)[:10]}")
