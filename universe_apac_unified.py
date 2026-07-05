import os, requests, csv, io, math, time
from datetime import datetime, timedelta

# ============================================================
# FORWARDALPHA — UNIVERSO ASIA PACIFIC UNIFICATO (5 MERCATI)
# Sostituisce update_universe_apac_jhk.py + update_universe_krx_sgx.py:
# un solo script per Giappone, Hong Kong, Australia, Corea, Singapore.
# Target fissi: TSE=1000, SEHK=500, ASX=350, KRX=400, SGX=100
# Ogni titolo deve anche avere un prezzo verificabile su Leeway, con
# backfill automatico dal prossimo candidato per mkt_cap se manca.
# ============================================================

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}

EX_MAP = {
    "TSE": "TSE", "TYO": "TSE", "XTKS": "TSE",
    "SEHK": "SEHK", "HKG": "SEHK", "XHKG": "SEHK",
    "ASX": "ASX", "XASX": "ASX",
    "KOSE": "KRX", "KOSDAQ": "KRX",
    "SGX": "SGX", "Catalist": "SGX", "NSE": "SGX", "SPSE": "SGX", "NSX": "SGX", "XKON": "SGX",
}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED"," LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES","WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
    "NEXT FUNDS","NIKKO ETF","DAIWA ETF","ONE ETF",           # emittenti ETF giapponesi
    "KOSPI","KOSDAQ","KODEX","TIGER","KBSTAR","ARIRANG",       # emittenti/indici coreani
    "HANARO","KOSEF","SMART","MIRAX","ACE ETF","SOL ETF",
    "INDEX","TRACKER",
]

CURRENCY_MAP = {"TSE":"JPY","SEHK":"HKD","ASX":"AUD","KRX":"KRW","SGX":"SGD"}
COUNTRY_DEF  = {"TSE":"JPN","SEHK":"HKG","ASX":"AUS","KRX":"KOR","SGX":"SGP"}
FLAG_MAP     = {"JPN":"🇯🇵","HKG":"🇭🇰","AUS":"🇦🇺","KOR":"🇰🇷","SGP":"🇸🇬"}

EXCHANGE_CRITERIA = {
    "TSE":  {"top_n": 1000},
    "SEHK": {"top_n": 500},
    "ASX":  {"top_n": 350},
    "KRX":  {"top_n": 400},
    "SGX":  {"top_n": 100},
}

def leeway_ticker(ticker, exchange):
    if exchange == "TSE":  return ticker + ".TSE"
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "ASX":  return ticker + ".AU"
    if exchange == "KRX":  return ticker.lstrip("A").zfill(6) + ".KO"
    if exchange == "SGX":  return ticker + ".SG"
    return ticker

def ha_prezzo_su_leeway(ticker, exchange):
    to_d = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    lt = leeway_ticker(ticker, exchange)
    try:
        url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return True
    except Exception:
        pass
    return False

def is_excluded(company):
    name = (company or "").upper()
    return any(kw in name for kw in ALWAYS_EXCLUDE)

def parse_mktcap(v):
    if not v: return None
    s = str(v).strip()
    s = s.replace("$","").strip()
    for suf in ("USDMM","EURMM","MM"):
        s = s.replace(suf,"")
    s = s.strip()
    if not s or s in ("-","N/A","nm"): return None
    # Formato osservato nel file TIKR: es. "$337,855.12MM"
    # virgola = separatore migliaia, punto = decimale (formato americano)
    s = s.replace(",","")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

print("=" * 60)
print("AGGIORNAMENTO IN_UNIVERSE — TUTTI I 5 MERCATI APAC (unificato)")
print("=" * 60)
print()

# Carica TIKR APAC (file unico)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv",
    headers=headers_r)
print(f"TIKR APAC: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
print(f"Colonne nel CSV: {reader.fieldnames}")
tikr_by_exchange = {ex: {} for ex in EXCHANGE_CRITERIA}
for row in reader:
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr_by_exchange: continue
    # SEHK: rimuovi zeri iniziali per il match (stessa regola di weekly_apac.py)
    raw_ticker = str(row.get("Ticker","")).strip()
    ticker = raw_ticker.lstrip("0") if exchange == "SEHK" else raw_ticker
    if not ticker: continue
    company = row.get("Company Name","").strip()
    mktcap  = parse_mktcap(row.get("Last Mkt Cap","") or row.get("Market Cap","") or row.get("Mkt Cap","") or row.get("MarketCap","") or row.get("Last Market Cap",""))
    sector  = row.get("Sector","").strip()
    country = row.get("Country","").strip()
    tikr_by_exchange[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "sector":sector,"country":country,"ex_raw":ex_raw
    }

for ex in EXCHANGE_CRITERIA:
    print(f"{ex} nel TIKR: {len(tikr_by_exchange[ex])}")
print()

total = 0

for exchange, criteria in EXCHANGE_CRITERIA.items():
    top_n = criteria["top_n"]
    tikr  = tikr_by_exchange[exchange]

    print(f"--- {exchange} ---")

    # Carica titoli già presenti nel DB per questo exchange
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

    # Candidati: esclude ETF/fondi, ordina per market cap
    candidati = []
    excl_count = 0
    for t, info in tikr.items():
        if is_excluded(info["company"]):
            excl_count += 1
            continue
        candidati.append((t, info["mkt_cap"] or 0))
    candidati.sort(key=lambda x: x[1], reverse=True)
    print(f"  Nel TIKR: {len(tikr)} — esclusi ETF/fondi: {excl_count}")
    print(f"  Verifico presenza su Leeway (target {top_n})...")

    eligible = []
    esclusi_no_leeway = []
    for t, mc in candidati:
        if len(eligible) >= top_n: break
        if ha_prezzo_su_leeway(t, exchange):
            eligible.append((t, mc))
        else:
            esclusi_no_leeway.append(t)
        time.sleep(0.1)
    eligible_tickers = [t for t, mc in eligible]

    print(f"  Eligible top {top_n} CON prezzo Leeway: {len(eligible)}")
    if esclusi_no_leeway:
        print(f"  Scartati senza prezzo Leeway: {len(esclusi_no_leeway)}")

    # Inserisci titoli nuovi non ancora nel DB (a blocchi da 100)
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
                print(f"  FAIL inserimento batch {i}: {r2.status_code} {r2.text[:150]}")
        print(f"  Inseriti {len(new_stocks)} nuovi titoli")

    # Aggiorna mkt_cap in fundamentals
    for t, mc in eligible:
        if not mc: continue
        requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up,
            params={"ticker":f"eq.{t}","exchange":f"eq.{exchange}"},
            json={"mkt_cap": mc})

    # Reset in_universe=false per l'intero exchange
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})

    # Set in_universe=true A BLOCCHI
    ok = 0
    CHUNK = 150
    for i in range(0, len(eligible_tickers), CHUNK):
        chunk = eligible_tickers[i:i+CHUNK]
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_up,
            params={"ticker": "in.(" + ",".join(chunk) + ")", "exchange": f"eq.{exchange}"},
            json={"in_universe": True})
        if r2.status_code in (200, 204):
            ok += len(chunk)
        else:
            print(f"  FAIL blocco in_universe {i}: {r2.status_code} {r2.text[:150]}")

    total += ok
    print(f"  in_universe=true: {ok}/{len(eligible_tickers)}")
    print()

print("=" * 60)
print(f"TOTALE APAC IN UNIVERSE (5 mercati): {total}")
print("Atteso: TSE=1000 + SEHK=500 + ASX=350 + KRX=400 + SGX=100 = 2350")
print("=" * 60)
