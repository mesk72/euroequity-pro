import os, requests, csv, io, math, time
from datetime import datetime, timedelta

# ============================================================
# FORWARDALPHA — UNIVERSO EUROPA UNIFICATO (16 MERCATI)
# Sostituisce update_universe_mil_lse.py + update_universe_eu_all.py:
# un solo script, una sola logica, per tutti i 16 mercati EU.
#
# Regola:
# - 6 mercati "grandi" (MIL,LSE,XETRA,PA,OM,SWX): soglia mkt_cap >= 400M,
#   nessun tetto sul numero di titoli
# - 7 mercati "medi" (AS,MC,BR,HE,CPSE,OB,GR): top 100 per mkt_cap
# - 3 mercati "piccoli" (VI,IR,LS): tutti (in pratica sempre sotto i 100)
#   — esclusi da value/growth/best score altrove (weekly_eu.py), ma
#   contati regolarmente in universo qui
#
# Ogni titolo, oltre a superare soglia/filtri, deve avere un prezzo
# verificabile su Leeway: altrimenti viene scartato e sostituito dal
# prossimo candidato per mkt_cap (backfill automatico sui mercati top-N).
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

# ── MAPPING EXCHANGE RAW TIKR -> FORWARDALPHA (16 mercati) ──────────
EX_MAP = {
    "BIT": "MIL",
    "LSE": "LSE",  # AIM escluso: mercato alternativo, non va fuso con LSE
    "XTRA": "XETRA", "HMSE": "XETRA", "DB": "XETRA", "MUN": "XETRA", "DUSE": "XETRA",
    "ENXTPA": "PA",
    "OM": "OM", "XSAT": "OM",  # NGM escluso: mercato alternativo, non va fuso con OM
    "SWX": "SWX", "BRSE": "SWX",
    "ENXTAM": "AS",
    "BME": "MC", "BDM": "MC",
    "ENXTBR": "BR",
    "HLSE": "HE",
    "CPSE": "CPSE",
    "OB": "OB", "OTCNO": "OB",
    "ATSE": "GR", "XATH": "GR", "ATH": "GR",
    "WBAG": "VI",
    "ISE": "IR",
    "ENXTLS": "LS",
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
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI","ISHARES MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
]

CURRENCY_MAP = {
    "MIL":"EUR","LSE":"GBP","XETRA":"EUR","PA":"EUR","OM":"SEK",
    "SWX":"CHF","AS":"EUR","MC":"EUR","BR":"EUR","HE":"EUR",
    "CPSE":"DKK","OB":"NOK","VI":"EUR","IR":"EUR","LS":"EUR","GR":"EUR",
}
FLAG_MAP = {
    "ITA":"🇮🇹","GBR":"🇬🇧","DEU":"🇩🇪","FRA":"🇫🇷","SWE":"🇸🇪",
    "CHE":"🇨🇭","NLD":"🇳🇱","ESP":"🇪🇸","BEL":"🇧🇪","FIN":"🇫🇮",
    "DNK":"🇩🇰","NOR":"🇳🇴","AUT":"🇦🇹","IRL":"🇮🇪","PRT":"🇵🇹","GRC":"🇬🇷",
}
COUNTRY_DEFAULT = {
    "MIL":"ITA","LSE":"GBR","XETRA":"DEU","PA":"FRA","OM":"SWE",
    "SWX":"CHE","AS":"NLD","MC":"ESP","BR":"BEL","HE":"FIN",
    "CPSE":"DNK","OB":"NOR","VI":"AUT","IR":"IRL","LS":"PRT","GR":"GRC",
}

# I 16 mercati EU, con la loro regola
EXCHANGE_CRITERIA = {
    "MIL":   {"min_cap": 400, "top_n": None},
    "LSE":   {"min_cap": 400, "top_n": None},
    "XETRA": {"min_cap": 400, "top_n": None},
    "PA":    {"min_cap": 400, "top_n": None},
    "OM":    {"min_cap": 400, "top_n": None},
    "SWX":   {"min_cap": 400, "top_n": None},
    "AS":    {"min_cap": None, "top_n": 100},
    "MC":    {"min_cap": None, "top_n": 100},
    "BR":    {"min_cap": None, "top_n": 100},
    "HE":    {"min_cap": None, "top_n": 100},
    "CPSE":  {"min_cap": None, "top_n": 100},
    "OB":    {"min_cap": None, "top_n": 100},
    "GR":    {"min_cap": None, "top_n": 100},
    "VI":    {"min_cap": None, "top_n": None},
    "IR":    {"min_cap": None, "top_n": None},
    "LS":    {"min_cap": None, "top_n": None},
}

# ── LEEWAY: formattazione ticker e verifica presenza ────────────────
SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}
LEEWAY_SUFFIX = {
    "MIL":  ".MI",    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":   ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":   ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":   ".IR",    "GR":    ".AT",
    "LSE":  ".LSE",   "SWX":   ".SW",
    "OM":   ".ST",    "OB":    ".OL",
    "CPSE": ".CO",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "OM": return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "BR": return ticker.replace(".", "") + ".BR"
    return ticker.rstrip(".") + LEEWAY_SUFFIX.get(exchange, "")

def ha_prezzo_su_leeway(ticker, exchange):
    """Verifica leggera (30gg). Per la Germania ritenta con .F se .XETRA fallisce."""
    to_d = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    candidati_lt = [leeway_ticker(ticker, exchange)]
    if exchange == "XETRA":
        candidati_lt.append(ticker.rstrip(".") + ".F")
    for lt in candidati_lt:
        try:
            url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    return True
        except Exception:
            continue
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
print("AGGIORNAMENTO IN_UNIVERSE — TUTTI I 16 MERCATI EU (unificato)")
print("=" * 60)
print()

# Carica TIKR EU
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"TIKR EU: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
print(f"Colonne nel CSV: {reader.fieldnames}")
tikr_by_exchange = {ex: {} for ex in EXCHANGE_CRITERIA}
mktcap_col_usata = None
for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr_by_exchange: continue
    company = row.get("Company Name","").strip()
    # Prova più nomi possibili per la colonna market cap (il file puo' cambiare formato)
    mktcap_raw = None
    for col in ("Last Mkt Cap", "Market Cap", "Mkt Cap", "MarketCap", "Last Market Cap"):
        if row.get(col):
            mktcap_raw = row.get(col)
            if mktcap_col_usata is None:
                mktcap_col_usata = col
            break
    mktcap  = parse_mktcap(mktcap_raw)
    country = row.get("Country","").strip()
    sector  = row.get("Sector","").strip()
    tikr_by_exchange[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "country":country,"sector":sector,"ex_raw":ex_raw
    }
print(f"Colonna market cap trovata e usata: {mktcap_col_usata}")

print()
total_eu = 0

for exchange, criteria in EXCHANGE_CRITERIA.items():
    min_cap = criteria["min_cap"]
    top_n   = criteria["top_n"]
    tikr    = tikr_by_exchange[exchange]

    print(f"--- {exchange} ---")
    print(f"  Nel TIKR: {len(tikr)}")

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
    print(f"  Nel DB: {len(stocks_db)}")

    # Candidati: esclude ETF/fondi e sotto-soglia, ordina per mkt_cap
    candidati = []
    excl_count = 0
    for t, info in tikr.items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]):
            excl_count += 1
            continue
        if min_cap and mc < min_cap: continue
        candidati.append((t, mc))
    candidati.sort(key=lambda x: x[1], reverse=True)
    print(f"  Esclusi ETF/fondi: {excl_count} — Candidati: {len(candidati)}")

    # Verifica Leeway in ordine di mkt_cap decrescente. Per i mercati a
    # soglia (top_n=None) filtra tutti i candidati; per i mercati top-N
    # si ferma al target, con backfill automatico dal prossimo per mkt_cap.
    eligible = []
    esclusi_no_leeway = []
    for t, mc in candidati:
        if top_n and len(eligible) >= top_n: break
        if ha_prezzo_su_leeway(t, exchange):
            eligible.append((t, mc))
        else:
            esclusi_no_leeway.append(t)
        time.sleep(0.1)
    eligible_tickers = [t for t, mc in eligible]

    label_n = str(top_n) if top_n else "tutti (soglia)"
    print(f"  Eligible ({label_n}) CON prezzo Leeway: {len(eligible)}")
    if esclusi_no_leeway:
        print(f"  Scartati senza prezzo Leeway: {len(esclusi_no_leeway)}")

    # Inserisci nuovi titoli
    new_stocks = []
    for t in eligible_tickers:
        if t not in stocks_db:
            info = tikr[t]
            country = info.get("country") or COUNTRY_DEFAULT.get(exchange,"")
            new_stocks.append({
                "ticker": t, "exchange": exchange,
                "company": info["company"],
                "sector": info["sector"],
                "country": country,
                "flag": FLAG_MAP.get(country, "🏳️"),
                "currency": CURRENCY_MAP.get(exchange,"EUR"),
                "in_universe": False,
                "primary_exchange": info["ex_raw"],
            })
    if new_stocks:
        for i in range(0, len(new_stocks), 100):
            batch = new_stocks[i:i+100]
            r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
                headers=headers_ins, json=batch)
            if r2.status_code not in (200,201):
                print(f"  FAIL inserimento batch {i}: {r2.status_code} {r2.text[:120]}")
        print(f"  Inseriti {len(new_stocks)} nuovi titoli")

    # Aggiorna mkt_cap in fundamentals — upsert, non PATCH (una PATCH
    # non tocca righe non ancora esistenti per titoli nuovi in universo)
    mkt_updates = [{"ticker": t, "exchange": exchange, "mkt_cap": mc} for t, mc in eligible if mc]
    for i in range(0, len(mkt_updates), 100):
        requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up, json=mkt_updates[i:i+100])

    # Reset in_universe=false per l'intero exchange
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})

    # Set in_universe=true A BLOCCHI
    ok = 0
    CHUNK = 100
    for i in range(0, len(eligible_tickers), CHUNK):
        chunk = eligible_tickers[i:i+CHUNK]
        r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_up,
            params={"ticker": "in.(" + ",".join(chunk) + ")", "exchange": f"eq.{exchange}"},
            json={"in_universe": True})
        if r2.status_code in (200, 204):
            ok += len(chunk)
        else:
            print(f"  FAIL blocco in_universe {i}: {r2.status_code} {r2.text[:120]}")

    total_eu += ok
    print(f"  in_universe=true: {ok}/{len(eligible_tickers)}")
    print()

print("=" * 60)
print(f"TOTALE EU IN UNIVERSE (16 mercati): {total_eu}")
print("=" * 60)
