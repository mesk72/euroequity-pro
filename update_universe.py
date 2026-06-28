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
    """Parsa mkt_cap da TIKR: es. "691.603,06 USDMM" → 691603.06"""
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    # Formato europeo: punto=migliaia, virgola=decimale
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
    "TSX":"TSX","TSXV":"TSX",
}

# Leggi file TIKR da Supabase Storage
print("=== AGGIORNAMENTO UNIVERSO DA TIKR ===")

all_tikr = {}  # (ticker, exchange) → mkt_cap

for fname, label in [("tikr_eu_latest.csv","EU"), ("tikr_na_latest.csv","NA")]:
    r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{fname}",
        headers=headers_r)
    if r.status_code != 200:
        print(f"  ERRORE lettura {fname}: {r.status_code}")
        continue
    reader = csv.DictReader(io.StringIO(r.text))
    count = 0
    for row in reader:
        ticker = row.get("Ticker","").strip()
        ex_raw = row.get("Primary Exchange","").strip()
        exchange = EX_MAP.get(ex_raw, ex_raw)
        mktcap = parse_mktcap(row.get("Last Mkt Cap",""))
        sector = row.get("Sector","").strip()
        company = row.get("Company Name","").strip()
        if not ticker or not exchange: continue
        all_tikr[(ticker, exchange)] = {
            "mkt_cap": mktcap,
            "sector": sector,
            "company": company,
            "excluded": is_excluded(company, sector)
        }
        count += 1
    print(f"  {label}: {count} titoli letti")

print(f"  Totale TIKR: {len(all_tikr)}")

# Aggiorna mkt_cap in stocks per tutti i titoli TIKR
print("\n=== AGGIORNAMENTO MKT_CAP IN STOCKS ===")
ok = fail = 0
for (ticker, exchange), info in all_tikr.items():
    if info["mkt_cap"] is None: continue
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
        json={"mkt_cap": info["mkt_cap"]})
    if r.status_code in (200,204): ok += 1
    else: fail += 1
print(f"  mkt_cap aggiornata: ok={ok} fail={fail}")

# Calcola nuovo universo
print("\n=== CALCOLO NUOVO UNIVERSO ===")

# Carica tutti i titoli dal DB
all_stocks = {}
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,mkt_cap,sector,company,in_universe",
                    "exchange": f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for s in batch:
            all_stocks[(s["ticker"], exchange)] = s
        offset += 1000
        if len(batch) < 1000: break

print(f"  Titoli nel DB: {len(all_stocks)}")

# Determina in_universe per ogni exchange
new_universe = set()

# EU grandi: mkt_cap >= 500M
for ex in ["LSE","XETRA","PA","OM","SWX","MIL"]:
    stocks = [(k,v) for k,v in all_stocks.items() if k[1]==ex]
    eligible = [(k,v) for k,v in stocks
                if not is_excluded(v.get("company",""), v.get("sector",""))
                and (v.get("mkt_cap") or 0) >= 500]
    for k,v in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (>= 500M)")

# EU medie: top 100
for ex in ["AS","MC","BR","HE","CPSE","OB"]:
    stocks = [(k,v) for k,v in all_stocks.items() if k[1]==ex]
    eligible = sorted(
        [(k,v) for k,v in stocks if not is_excluded(v.get("company",""), v.get("sector",""))],
        key=lambda x: x[1].get("mkt_cap") or 0, reverse=True)[:100]
    for k,v in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (top 100)")

# EU piccole: tutti
for ex in ["VI","IR","LS"]:
    stocks = [(k,v) for k,v in all_stocks.items() if k[1]==ex]
    eligible = [(k,v) for k,v in stocks
                if not is_excluded(v.get("company",""), v.get("sector",""))]
    for k,v in eligible:
        new_universe.add(k)
    print(f"  {ex}: {len(eligible)} titoli (tutti)")

# US: top 2500
stocks_us = [(k,v) for k,v in all_stocks.items() if k[1]=="US"]
eligible_us = sorted(
    [(k,v) for k,v in stocks_us if not is_excluded(v.get("company",""), v.get("sector",""))],
    key=lambda x: x[1].get("mkt_cap") or 0, reverse=True)[:2500]
for k,v in eligible_us:
    new_universe.add(k)
print(f"  US: {len(eligible_us)} titoli (top 2500)")

# TSX: top 500
stocks_tsx = [(k,v) for k,v in all_stocks.items() if k[1]=="TSX"]
eligible_tsx = sorted(
    [(k,v) for k,v in stocks_tsx if not is_excluded(v.get("company",""), v.get("sector",""))],
    key=lambda x: x[1].get("mkt_cap") or 0, reverse=True)[:500]
for k,v in eligible_tsx:
    new_universe.add(k)
print(f"  TSX: {len(eligible_tsx)} titoli (top 500)")

print(f"\n  TOTALE NUOVO UNIVERSO: {len(new_universe)}")

# Aggiorna in_universe nel DB
print("\n=== AGGIORNAMENTO IN_UNIVERSE ===")

# Prima reset tutti a false
for exchange in ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","VI","IR","LS","US","TSX"]:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange": f"eq.{exchange}"},
        json={"in_universe": False})
    print(f"  Reset {exchange}: {r.status_code}")

# Poi set true per i titoli del nuovo universo
ok = fail = 0
for ticker, exchange in new_universe:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
        json={"in_universe": True})
    if r.status_code in (200,204): ok += 1
    else: fail += 1

print(f"\n  in_universe=true: ok={ok} fail={fail}")
print("\n=== DONE ===")
print("Ora lancia Weekly EU Load e Weekly US Load.")
