import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}

EX_MAP = {"BIT":"MIL","LSE":"LSE"}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES GOLD","ISHARES SILVER","ISHARES PHYSICAL",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI","ISHARES MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
]

CURRENCY_MAP = {"MIL":"EUR","LSE":"GBP"}
COUNTRY_DEFAULT = {"MIL":"ITA","LSE":"GBR"}
FLAG_MAP = {"ITA":"🇮🇹","GBR":"🇬🇧"}

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

print("=== AGGIORNAMENTO IN_UNIVERSE — SOLO MIL E LSE ===")
print()

# Carica file TIKR EU
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

tikr = {"MIL":{}, "LSE":{}}
for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr: continue
    company = row.get("Company Name","").strip()
    mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
    country = row.get("Country","").strip()
    sector  = row.get("Sector","").strip()
    tikr[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "country":country,"sector":sector,"ex_raw":ex_raw
    }

for exchange in ["MIL","LSE"]:
    print(f"--- {exchange} ---")

    # Carica titoli esistenti nel DB
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

    print(f"  Nel DB: {len(stocks_db)}")

    # Calcola eligible
    eligible = []
    for t, info in tikr[exchange].items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]): continue
        if mc < 400: continue
        eligible.append(t)

    print(f"  Eligible (>=400M non esclusi): {len(eligible)}")

    # Inserisci nuovi titoli mancanti
    new_stocks = []
    for t in eligible:
        if t not in stocks_db:
            info = tikr[exchange][t]
            new_stocks.append({
                "ticker": t, "exchange": exchange,
                "company": info["company"],
                "sector": info["sector"],
                "country": info.get("country") or COUNTRY_DEFAULT[exchange],
                "flag": FLAG_MAP.get(info.get("country") or COUNTRY_DEFAULT[exchange], "🏳️"),
                "currency": CURRENCY_MAP[exchange],
                "in_universe": False,
                "primary_exchange": info["ex_raw"],
            })

    if new_stocks:
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_ins, json=new_stocks)
        print(f"  Inseriti {len(new_stocks)} nuovi titoli: HTTP {r2.status_code}")

    # Aggiorna mkt_cap in fundamentals
    ok = fail = 0
    for t in eligible:
        mc = tikr[exchange][t]["mkt_cap"]
        if not mc: continue
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"mkt_cap": mc})
        if r2.status_code in (200,204): ok += 1
        else: fail += 1
    print(f"  mkt_cap aggiornata: ok={ok} fail={fail}")

    # Reset in_universe=false per exchange
    r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})
    print(f"  Reset in_universe=false: HTTP {r2.status_code}")

    # Set in_universe=true per eligible
    ok = fail = 0
    for t in eligible:
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"in_universe": True})
        if r2.status_code in (200,204): ok += 1
        else: fail += 1
    print(f"  in_universe=true: ok={ok} fail={fail}")
    print()

print("=== DONE ===")
print("Verifica: MIL dovrebbe avere 115, LSE 424")
