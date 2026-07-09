import os, requests, csv, io, time
from datetime import datetime, timezone

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance")

# Stesso suffisso Yahoo usato per la selezione universo (confermati:
# SR/QA/KW/AE; da verificare: OM/BH — pochi titoli, 47 su 500)
GCC_SUFFIX = {
    "SASE": ".SR", "DSM": ".QA", "KWSE": ".KW",
    "ADX": ".AE", "DFM": ".AE", "DIFX": ".AE",
    "MSM": ".OM", "BAX": ".BH",
}

print("=" * 60)
print("[1/3] Ticker GCC dal file TIKR (tutti i 500, indipendente")
print("      dall'universo — non serve una riga in stocks)")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_gcc_latest.csv", headers=headers_r)
print(f"  HTTP {r.status_code}")
reader = csv.DictReader(io.StringIO(r.text))
candidati = []
for row in reader:
    prim_ex = row.get("Primary Exchange","").strip()
    ticker  = row.get("Ticker","").strip()
    company = row.get("Company Name","").strip()
    if not ticker or prim_ex not in GCC_SUFFIX: continue
    yt = ticker + GCC_SUFFIX[prim_ex]
    candidati.append((ticker, prim_ex, company, yt))
print(f"  Candidati totali: {len(candidati)}")

print()
print("=" * 60)
print("[2/3] Download da Yahoo: fiscal year end + website")
print("=" * 60)
fy_results = []
web_results = []
not_found_fy = []
not_found_web = []
t0 = time.time()
for i, (ticker, prim_ex, company, yt) in enumerate(candidati):
    try:
        info = yf.Ticker(yt).info
        ts = info.get("lastFiscalYearEnd") or info.get("nextFiscalYearEnd")
        if ts:
            month = datetime.fromtimestamp(ts, tz=timezone.utc).month
            fy_results.append({"ticker": ticker, "exchange": "GCC", "fiscal_month": month})
        else:
            not_found_fy.append(yt)
        website = info.get("website")
        if website:
            web_results.append({"ticker": ticker, "exchange": "GCC", "website": website})
        else:
            not_found_web.append(yt)
    except Exception:
        not_found_fy.append(yt)
        not_found_web.append(yt)
    if (i+1) % 50 == 0:
        elapsed = time.time() - t0
        print(f"  ...{i+1}/{len(candidati)} ({elapsed/60:.1f} min) — fy={len(fy_results)} web={len(web_results)}")
    time.sleep(0.15)

print(f"\n  Fiscal year end trovati: {len(fy_results)}/{len(candidati)}")
print(f"  Website trovati: {len(web_results)}/{len(candidati)}")
if not_found_fy:
    print(f"  FY non trovato (esempio 15): {not_found_fy[:15]}")

print()
print("=" * 60)
print("[3/3] Scrittura CSV")
print("=" * 60)
with open("fiscal_year_end_gcc.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","fiscal_month"])
    w.writeheader()
    for row in fy_results: w.writerow(row)
print(f"  Scritto fiscal_year_end_gcc.csv ({len(fy_results)} righe)")

with open("website_gcc.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","website"])
    w.writeheader()
    for row in web_results: w.writerow(row)
print(f"  Scritto website_gcc.csv ({len(web_results)} righe)")
print("\nFATTO.")
