import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "return=minimal"}

EX_MAP = {
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "ARCA":"US","OTCPK":"US","NYSEAM":"US",
    "TSX":"TSX","TSXV":"TSX","CNSX":"TSX","NEOE":"TSX",
    "MutualFund": None,
}

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

CURRENCY_MAP = {"US":"USD","TSX":"CAD"}
COUNTRY_DEFAULT = {"US":"USA","TSX":"CAN"}
FLAG_MAP = {"USA":"🇺🇸","CAN":"🇨🇦"}

# US top 2000 netti, TSX top 400 netti
EXCHANGE_CRITERIA = {
    "US":  {"top_n": 2000},
    "TSX": {"top_n": 400},
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

print("=== AGGIORNAMENTO IN_UNIVERSE NA (US + TSX) ===")
print()

# Carica TIKR NA
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
print(f"TIKR NA: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
tikr_by_exchange = {"US":{}, "TSX":{}}

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

print(f"US nel TIKR: {len(tikr_by_exchange['US'])}")
print(f"TSX nel TIKR: {len(tikr_by_exchange['TSX'])}")
print()

total_na = 0

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

    # Calcola eligible — escludi ETF/fondi poi ordina per mkt_cap
    eligible = []
    for t, info in tikr.items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]): continue
        eligible.append((t, mc))

    eligible.sort(key=lambda x: x[1], reverse=True)
    eligible = eligible[:top_n]
    eligible_tickers = [t for t,mc in eligible]

    excl_count = len(tikr) - len([t for t in tikr if not is_excluded(tikr[t]["company"])])
    print(f"  Nel TIKR: {len(tikr)} — esclusi ETF/fondi: {excl_count}")
    print(f"  Eligible top {top_n}: {len(eligible)}")

    # Inserisci nuovi titoli
    new_stocks = []
    for t in eligible_tickers:
        if t not in stocks_db:
            info = tikr[t]
            country = info.get("country") or COUNTRY_DEFAULT[exchange]
            new_stocks.append({
                "ticker": t, "exchange": exchange,
                "company": info["company"],
                "sector": info["sector"],
                "country": country,
                "flag": FLAG_MAP.get(country, FLAG_MAP[COUNTRY_DEFAULT[exchange]]),
                "currency": CURRENCY_MAP[exchange],
                "in_universe": False,
                "primary_exchange": info["ex_raw"],
            })

    if new_stocks:
        # Inserisci in batch da 100
        for i in range(0, len(new_stocks), 100):
            batch = new_stocks[i:i+100]
            r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
                headers=headers_ins, json=batch)
            if r2.status_code not in (200,201):
                print(f"  FAIL inserimento batch {i}: {r2.status_code} {r2.text[:100]}")
        print(f"  Inseriti {len(new_stocks)} nuovi titoli")

    # Aggiorna mkt_cap in fundamentals
    for t, mc in eligible:
        if not mc: continue
        requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"mkt_cap": mc})

    # Reset in_universe=false per exchange
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})

    # Set in_universe=true per eligible
    ok = fail = 0
    for t in eligible_tickers:
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"in_universe": True})
        if r2.status_code in (200,204): ok += 1
        else: fail += 1

    total_na += ok
    print(f"  in_universe=true: {ok} fail={fail}")
    print()

print(f"=== TOTALE NA IN UNIVERSE: {total_na} ===")
print(f"Atteso: US=2000 + TSX=400 = 2400")
