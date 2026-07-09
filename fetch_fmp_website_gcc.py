import os, requests, csv, io, time

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
FMP_KEY = "aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

GCC_SUFFIX = {
    "SASE": ".SR", "DSM": ".QA", "KWSE": ".KW",
    "ADX": ".AE", "DFM": ".AE", "DIFX": ".AE",
    "MSM": ".OM", "BAX": ".BH",
}

print("=" * 60)
print("[1/3] Elenco 500 candidati GCC dal TIKR")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_gcc_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
all_candidati = {}
for row in reader:
    prim_ex = row.get("Primary Exchange","").strip()
    ticker  = row.get("Ticker","").strip()
    if not ticker or prim_ex not in GCC_SUFFIX: continue
    all_candidati[ticker] = ticker + GCC_SUFFIX[prim_ex]
print(f"  Candidati totali: {len(all_candidati)}")

print()
print("=" * 60)
print("[2/3] Chi ha gia' il website da Yahoo (gap da riempire)")
print("=" * 60)
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/website_gcc.csv", headers=headers_r)
already = set()
if r2.status_code == 200:
    reader2 = csv.DictReader(io.StringIO(r2.text))
    for row in reader2:
        already.add(row.get("ticker","").strip())
print(f"  Gia' trovati da Yahoo: {len(already)}")
gap = {t: yt for t, yt in all_candidati.items() if t not in already}
print(f"  Da recuperare con FMP: {len(gap)}")

print()
print("=" * 60)
print("[3/3] Download website da FMP per il gap")
print("=" * 60)
results = []
not_found = []
for i, (ticker, fmp_symbol) in enumerate(gap.items()):
    try:
        resp = requests.get(f"https://financialmodelingprep.com/stable/profile?symbol={fmp_symbol}&apikey={FMP_KEY}", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data and data[0].get("website"):
                results.append({"ticker": ticker, "exchange": "GCC", "website": data[0]["website"]})
            else:
                not_found.append(fmp_symbol)
        else:
            not_found.append(f"{fmp_symbol} (HTTP {resp.status_code})")
    except Exception as e:
        not_found.append(f"{fmp_symbol} (ERR {e})")
    if (i+1) % 25 == 0:
        print(f"  ...{i+1}/{len(gap)} — trovati={len(results)}")
    time.sleep(0.3)

print(f"\n  Trovati con FMP: {len(results)}/{len(gap)}")
if not_found:
    print(f"  Non trovati (esempio 15): {not_found[:15]}")

with open("website_gcc_fmp_addon.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ticker","exchange","website"])
    w.writeheader()
    for row in results: w.writerow(row)
print(f"\n  Scritto website_gcc_fmp_addon.csv ({len(results)} righe)")
print(f"  Copertura totale attesa: {len(already)} (Yahoo) + {len(results)} (FMP) = {len(already)+len(results)}/{len(all_candidati)}")
print("FATTO.")
