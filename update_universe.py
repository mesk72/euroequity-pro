import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EXCLUDE_NAMES = [
    "ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]
EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()
    return any(kw in name for kw in EXCLUDE_NAMES)

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if not math.isnan(f) else None
    except: return None

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","DB":"XETRA","DUSE":"XETRA",
    "MUN":"XETRA","BRSE":"BR","HMSE":"OM","XSAT":"OM",
    "OTCNO":"OB","SWX":"SWX","LSE":"LSE","CPSE":"CPSE",
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "TSX":"TSX","TSXV":"TSX",
}

print("=== AGGIORNAMENTO UNIVERSO DA TIKR ===")

# Leggi file TIKR e aggiorna mkt_cap in fundamentals
all_tikr = {}
for fname, label in [("tikr_eu_latest.csv","EU"), ("tikr_na_latest.csv","NA")]:
    r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{fname}",
        headers=headers_r)
    if r.status_code != 200:
        print(f"  ERRORE lettura {fname}: {r.status_code} {r.text[:100]}")
        continue
    reader = csv.DictReader(io.StringIO(r.text))
    count = 0
    for row in reader:
        ticker  = row.get("Ticker","").strip()
        ex_raw  = row.get("Primary Exchange","").strip()
        exchange = EX_MAP.get(ex_raw, ex_raw)
        mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
        sector  = row.get("Sector","").strip()
        company = row.get("Company Name","").strip()
        if not ticker or not exchange: continue
        all_tikr[(ticker, exchange)] = {
            "mkt_cap": mktcap,
            "sector": sector,
            "company": company,
        }
        count += 1
    print(f"  {label}: {count} titoli letti")

print(f"  Totale TIKR: {len(all_tikr)}")

# Aggiorna mkt_cap in FUNDAMENTALS (non stocks)
print("\n=== AGGIORNAMENTO MKT_CAP IN FUNDAMENTALS ===")
ok = fail = skip = 0
for (ticker, exchange), info in all_tikr.items():
    if info["mkt_cap"] is None:
        skip += 1
        continue
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
        json={"mkt_cap": info["mkt_cap"]})
    if r.status_code in (200,204): ok += 1
    else:
        fail += 1
        if fail <= 3:
            print(f"  FAIL {exchange} {ticker}: {r.status_code} {r.text[:100]}")
print(f"  mkt_cap aggiornata: ok={ok} fail={fail} skip={skip}")

# Carica mkt_cap aggiornata da fundamentals per calcolare universo
print("\n=== CARICA MKT_CAP DA FUNDAMENTALS ===")
mktcap_map = {}
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,mkt_cap",
                    "exchange": f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for s in batch:
            mktcap_map[(s["ticker"], s["exchange"])] = s.get("mkt_cap") or 0
        offset += 1000
        if len(batch) < 1000: break

print(f"  Titoli con mkt_cap: {sum(1 for v in mktcap_map.values() if v > 0)}")

# Carica stocks per company e sector
print("\n=== CARICA STOCKS PER ESCLUSIONI ===")
stocks_info = {}
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,company,sector",
                    "exchange": f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for s in batch:
            stocks_info[(s["ticker"], s["exchange"])] = s
        offset += 1000
        if len(batch) < 1000: break

print(f"  Totale stocks nel DB: {len(stocks_info)}")

# Calcola nuovo universo
print("\n=== CALCOLO NUOVO UNIVERSO ===")
new_universe = set()

def get_eligible(exchange, min_cap=None, top_n=None):
    keys = [(t,e) for (t,e) in stocks_info if e == exchange]
    result = []
    for k in keys:
        s = stocks_info[k]
        mc = mktcap_map.get(k, 0)
        if is_excluded(s.get("company",""), s.get("sector","")):
            continue
        if min_cap and mc < min_cap:
            continue
        result.append((k, mc))
    result.sort(key=lambda x: x[1], reverse=True)
    if top_n:
        result = result[:top_n]
    return result

# EU grandi
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    eligible = get_eligible(ex, min_cap=500)
    for k, mc in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (>= 500M)")

# EU medie
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    eligible = get_eligible(ex, top_n=100)
    for k, mc in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (top 100)")

# EU piccole
for ex in ["VI","IR","LS"]:
    eligible = get_eligible(ex)
    for k, mc in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (tutti)")

# US
eligible_us = get_eligible("US", top_n=2500)
for k, mc in eligible_us:
    new_universe.add(k)
print(f"  US: {len(eligible_us)} titoli (top 2500)")

# TSX
eligible_tsx = get_eligible("TSX", top_n=500)
for k, mc in eligible_tsx:
    new_universe.add(k)
print(f"  TSX: {len(eligible_tsx)} titoli (top 500)")

print(f"\n  TOTALE NUOVO UNIVERSO: {len(new_universe)}")

# Aggiorna in_universe nel DB
print("\n=== AGGIORNAMENTO IN_UNIVERSE ===")

# Reset tutti a false
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange": f"eq.{exchange}"},
        json={"in_universe": False})

print(f"  Reset in_universe=false: OK")

# Set true per nuovo universo
ok = fail = 0
for ticker, exchange in new_universe:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
        json={"in_universe": True})
    if r.status_code in (200,204): ok += 1
    else:
        fail += 1
        if fail <= 3:
            print(f"  FAIL {exchange} {ticker}: {r.status_code} {r.text[:100]}")

print(f"  in_universe=true: ok={ok} fail={fail}")
print("\n=== DONE ===")
print("Ora lancia Weekly EU Load e Weekly US Load.")
