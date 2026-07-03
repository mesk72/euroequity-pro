import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}

# Mapping exchange raw → ForwardAlpha
EX_MAP = {
    # Corea
    "KOSE":"KRX","KOSDAQ":"KRX",
    # Singapore
    "SGX":"SGX","Catalist":"SGX",
    "NSE":"SGX","SPSE":"SGX","NSX":"SGX","XKON":"SGX",
}

# KRX: escludi ETF fondi MSCI KOSPI KOSDAQ index
ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","PHYSICAL GOLD","PHYSICAL SILVER",
    "INDEX FUND","BOND FUND","MUTUAL FUND","MUTUALFUND",
    "KOSPI","KOSDAQ","KODEX","TIGER","KBSTAR","ARIRANG",
    "HANARO","KOSEF","SMART","MIRAX","ACE ETF","SOL ETF",
    "MSCI ","INDEX","TRACKER","XTRACKERS","WISDOMTREE ETF",
    "VANECK ETF","ISHARES","SPDR ETF","INVESCO DB ",
    "SICAV","ICAV",
]

CURRENCY_MAP  = {"KRX":"KRW","SGX":"SGD"}
COUNTRY_DEF   = {"KRX":"KOR","SGX":"SGP"}
FLAG_MAP       = {"KOR":"🇰🇷","SGP":"🇸🇬"}

# KRX top 400, SGX top 100
EXCHANGE_CRITERIA = {
    "KRX": {"top_n": 400},
    "SGX": {"top_n": 100},
}

def is_excluded(company):
    name = (company or "").upper()
    return any(kw in name for kw in ALWAYS_EXCLUDE)

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

print("=== AGGIORNAMENTO IN_UNIVERSE KRX E SGX ===")
print()

# Carica TIKR APAC
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv",
    headers=headers_r)
print(f"TIKR APAC: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
tikr_by_exchange = {"KRX":{}, "SGX":{}}

for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr_by_exchange: continue
    company = row.get("Company Name","").strip()
    mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
    sector  = row.get("Sector","").strip()
    country = row.get("Country","").strip()
    tikr_by_exchange[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "sector":sector,"country":country,"ex_raw":ex_raw
    }

print(f"KRX nel TIKR: {len(tikr_by_exchange['KRX'])}")
print(f"SGX nel TIKR: {len(tikr_by_exchange['SGX'])}")
print()

total = 0

for exchange, criteria in EXCHANGE_CRITERIA.items():
    top_n = criteria["top_n"]
    tikr  = tikr_by_exchange[exchange]

    # Carica titoli DB
    stocks_db = {}
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,company","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: stocks_db[s["ticker"]] = s
        offset += 1000
        if len(batch)<1000: break

    print(f"--- {exchange} ---")
    print(f"  Nel DB: {len(stocks_db)}")

    # Calcola eligible
    eligible = []
    excl_count = 0
    for t, info in tikr.items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]):
            excl_count += 1
            continue
        eligible.append((t, mc))

    eligible.sort(key=lambda x: x[1], reverse=True)
    eligible = eligible[:top_n]
    eligible_tickers = [t for t,mc in eligible]

    print(f"  Nel TIKR: {len(tikr)} — esclusi ETF/indici: {excl_count}")
    print(f"  Eligible top {top_n}: {len(eligible)}")

    # Inserisci nuovi titoli
    new_stocks = []
    for t in eligible_tickers:
        if t not in stocks_db:
            info = tikr[t]
            country = info.get("country") or COUNTRY_DEF[exchange]
            new_stocks.append({
                "ticker": t, "exchange": exchange,
                "company": info["company"],
                "sector": info["sector"],
                "country": country,
                "flag": FLAG_MAP.get(country, FLAG_MAP[COUNTRY_DEF[exchange]]),
                "currency": CURRENCY_MAP[exchange],
                "in_universe": False,
                "primary_exchange": info["ex_raw"],
            })

    if new_stocks:
        for i in range(0, len(new_stocks), 100):
            batch = new_stocks[i:i+100]
            r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
                headers=headers_ins, json=batch)
            if r2.status_code not in (200,201):
                print(f"  FAIL batch {i}: {r2.status_code} {r2.text[:100]}")
        print(f"  Inseriti {len(new_stocks)} nuovi titoli")

    # Aggiorna mkt_cap in fundamentals
    for t, mc in eligible:
        if not mc: continue
        requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"mkt_cap": mc})

    # Reset in_universe=false
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})

    # Set in_universe=true
    ok = fail = 0
    for t in eligible_tickers:
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"in_universe": True})
        if r2.status_code in (200,204): ok += 1
        else: fail += 1

    total += ok
    print(f"  in_universe=true: {ok} fail={fail}")
    print()

print(f"=== TOTALE KRX+SGX IN UNIVERSE: {total} ===")
print(f"Atteso: KRX=400 + SGX=100 = 500")
