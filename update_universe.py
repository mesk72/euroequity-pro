import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "return=minimal"}

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

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

def parse_num(v):
    if not v: return None
    s = str(v).replace("x","").replace("%","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if not math.isnan(f) else None
    except: return None

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","SWX":"SWX","LSE":"LSE","CPSE":"CPSE",
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "TSX":"TSX","TSXV":"TSX","OB":"OB","OTCNO":"OB",
    "HMSE":"OM","XSAT":"OM","OM":"OM",
}

COUNTRY_FLAG = {
    "USA":"🇺🇸","CAN":"🇨🇦","GBR":"🇬🇧","DEU":"🇩🇪","FRA":"🇫🇷",
    "ITA":"🇮🇹","SWE":"🇸🇪","CHE":"🇨🇭","NLD":"🇳🇱","BEL":"🇧🇪",
    "ESP":"🇪🇸","FIN":"🇫🇮","DNK":"🇩🇰","NOR":"🇳🇴","AUT":"🇦🇹",
    "IRL":"🇮🇪","PRT":"🇵🇹","NLD":"🇳🇱",
}

CURRENCY_MAP = {
    "US":"USD","TSX":"CAD","LSE":"GBP","XETRA":"EUR","PA":"EUR",
    "MIL":"EUR","AS":"EUR","MC":"EUR","BR":"EUR","HE":"EUR",
    "CPSE":"DKK","OB":"NOK","OM":"SEK","SWX":"CHF","VI":"EUR",
    "IR":"EUR","LS":"EUR",
}

print("=== CARICA STOCKS ESISTENTI DAL DB ===")
existing = set()
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: existing.add((s["ticker"],s["exchange"]))
        offset += 1000
        if len(batch)<1000: break
print(f"  Titoli esistenti: {len(existing)}")

# Leggi TIKR e trova nuovi titoli
print("\n=== LEGGI TIKR E INSERISCI NUOVI TITOLI ===")
all_tikr = {}
new_stocks = []

for fname, label in [("tikr_eu_latest.csv","EU"),("tikr_na_latest.csv","NA")]:
    r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{fname}",
        headers=headers_r)
    if r.status_code != 200:
        print(f"  ERRORE {fname}: {r.status_code}")
        continue
    reader = csv.DictReader(io.StringIO(r.text))
    count = new = 0
    for row in reader:
        ticker  = row.get("Ticker","").strip()
        ex_raw  = row.get("Primary Exchange","").strip()
        exchange = EX_MAP.get(ex_raw, ex_raw)
        company = row.get("Company Name","").strip()
        sector  = row.get("Sector","").strip()
        country = row.get("Country","").strip()
        mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
        if not ticker or not exchange: continue

        all_tikr[(ticker,exchange)] = {
            "mkt_cap": mktcap, "sector": sector,
            "company": company, "country": country,
        }
        count += 1

        # Inserisci se non esiste
        if (ticker,exchange) not in existing:
            new_stocks.append({
                "ticker": ticker,
                "exchange": exchange,
                "company": company,
                "sector": sector,
                "country": country,
                "flag": COUNTRY_FLAG.get(country,"🏳️"),
                "currency": CURRENCY_MAP.get(exchange,"USD"),
                "in_universe": False,
                "primary_exchange": ex_raw,
            })
            new += 1
    print(f"  {label}: {count} titoli letti, {new} nuovi da inserire")

# Inserisci nuovi titoli in batch
print(f"\n  Inserimento {len(new_stocks)} nuovi titoli...")
inserted = failed = 0
BATCH = 100
for i in range(0, len(new_stocks), BATCH):
    batch = new_stocks[i:i+BATCH]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_ins, json=batch)
    if r.status_code in (200,201): inserted += len(batch)
    else:
        failed += len(batch)
        if failed <= 3:
            print(f"  FAIL batch {i}: {r.status_code} {r.text[:100]}")
print(f"  Inseriti: {inserted} Falliti: {failed}")

# Aggiorna mkt_cap in fundamentals
print("\n=== AGGIORNAMENTO MKT_CAP IN FUNDAMENTALS ===")
ok = fail = skip = 0
for (ticker,exchange), info in all_tikr.items():
    if info["mkt_cap"] is None:
        skip += 1
        continue
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
        headers=headers_up,
        params={"ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"},
        json={"mkt_cap": info["mkt_cap"]})
    if r.status_code in (200,204): ok += 1
    else:
        fail += 1
        if fail<=3: print(f"  FAIL {exchange} {ticker}: {r.status_code}")
print(f"  mkt_cap: ok={ok} fail={fail} skip={skip}")

# Ricarica stocks aggiornati
print("\n=== RICARICA STOCKS ===")
stocks_info = {}
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,company,sector",
                    "exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: stocks_info[(s["ticker"],s["exchange"])] = s
        offset += 1000
        if len(batch)<1000: break
print(f"  Totale stocks: {len(stocks_info)}")

# Carica mkt_cap da fundamentals
mktcap_map = {}
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,mkt_cap","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: mktcap_map[(s["ticker"],s["exchange"])] = s.get("mkt_cap") or 0
        offset += 1000
        if len(batch)<1000: break
print(f"  Con mkt_cap > 0: {sum(1 for v in mktcap_map.values() if v>0)}")

# Calcola nuovo universo
print("\n=== CALCOLO NUOVO UNIVERSO ===")
new_universe = set()

def get_eligible(exchange, min_cap=None, top_n=None):
    keys = [(t,e) for (t,e) in stocks_info if e==exchange]
    result = []
    for k in keys:
        s = stocks_info[k]
        mc = mktcap_map.get(k,0)
        if is_excluded(s.get("company",""), s.get("sector","")): continue
        if min_cap and mc < min_cap: continue
        result.append((k,mc))
    result.sort(key=lambda x: x[1], reverse=True)
    if top_n: result = result[:top_n]
    return result

for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    el = get_eligible(ex, min_cap=400)
    for k,mc in el: new_universe.add(k)
    print(f"  {ex}: {len(el)} (>=500M)")

for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    el = get_eligible(ex, top_n=100)
    for k,mc in el: new_universe.add(k)
    print(f"  {ex}: {len(el)} (top 100)")

for ex in ["VI","IR","LS"]:
    el = get_eligible(ex)
    for k,mc in el: new_universe.add(k)
    print(f"  {ex}: {len(el)} (tutti)")

el_us = get_eligible("US", top_n=2500)
for k,mc in el_us: new_universe.add(k)
print(f"  US: {len(el_us)} (top 2500)")

el_tsx = get_eligible("TSX", top_n=500)
for k,mc in el_tsx: new_universe.add(k)
print(f"  TSX: {len(el_tsx)} (top 500)")

print(f"\n  TOTALE: {len(new_universe)}")

# Aggiorna in_universe
print("\n=== AGGIORNAMENTO IN_UNIVERSE ===")
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})
print("  Reset OK")

ok = fail = 0
for ticker, exchange in new_universe:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"},
        json={"in_universe": True})
    if r.status_code in (200,204): ok += 1
    else: fail += 1
print(f"  in_universe=true: ok={ok} fail={fail}")
print("\n=== DONE — ora lancia Weekly EU e Weekly US ===")
