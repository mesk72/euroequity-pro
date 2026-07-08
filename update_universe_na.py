import os, requests, csv, io, math, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
headers_ins = {**headers_r, "Content-Type": "application/json",
               "Prefer": "resolution=ignore-duplicates,return=minimal"}

SPECIAL_TICKERS_US = {
    "BRK.A": "BRK-B",  # Leeway copre solo la classe B, più liquida
}

def leeway_ticker(ticker, exchange):
    if exchange == "TSX":
        return ticker.replace(".", "-") + ".TO"
    if ticker in SPECIAL_TICKERS_US:
        return SPECIAL_TICKERS_US[ticker] + ".US"
    return ticker.rstrip(".").replace(".", "-") + ".US"

def ha_prezzo_su_leeway(ticker, exchange):
    """Verifica leggera (30gg) — 3 tentativi con backoff: senza retry un
    timeout transitorio scarta per sempre un titolo valido, ed e' questo
    che faceva fermare US a ~1979 invece di 2000."""
    to_d = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    lt = leeway_ticker(ticker, exchange)
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return isinstance(data, list) and bool(data)
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1)); continue
            return False  # 404 e simili: risposta definitiva
        except Exception:
            if attempt < 2: time.sleep(2 * (attempt + 1))
    return False

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
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED"," LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","ISHARES","WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND","INVESCO DB ",
    "SICAV","ICAV"," MSCI ","YOURINDEX","ETFS EUR","ETFS USD",
    "BNP PARIBAS EASY","AMUNDI MSCI","LYXOR MSCI","ISHARES MSCI",
    "EASY MSCI","YIS MSCI","WISDOMTREE ISSUER",
]

CURRENCY_MAP = {"US":"USD","TSX":"CAD"}
COUNTRY_DEFAULT = {"US":"USA","TSX":"CAN"}
FLAG_MAP = {"USA":"🇺🇸","CAN":"🇨🇦"}

# US top 3000 netti, TSX top 400 netti (soglia US alzata 08/07/2026:
# nuovo file TIKR con 3500 candidati USA / 500 candidati Canada)
EXCHANGE_CRITERIA = {
    "US":  {"top_n": 3000},
    "TSX": {"top_n": 400},
}

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

print("=== AGGIORNAMENTO IN_UNIVERSE NA (US + TSX) ===")
print()

# Carica TIKR NA
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers=headers_r)
print(f"TIKR NA: HTTP {r.status_code} — {len(r.text.splitlines())} righe")

reader = csv.DictReader(io.StringIO(r.text))
print(f"Colonne nel CSV: {reader.fieldnames}")
tikr_by_exchange = {"US":{}, "TSX":{}}
mktcap_col_usata = None

for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr_by_exchange: continue
    company = row.get("Company Name","").strip()
    mktcap_raw = None
    for col in ("Last Mkt Cap", "Market Cap", "Mkt Cap", "MarketCap", "Last Market Cap"):
        if row.get(col):
            mktcap_raw = row.get(col)
            if mktcap_col_usata is None:
                mktcap_col_usata = col
            break
    mktcap  = parse_mktcap(mktcap_raw)
    sector  = row.get("Sector","").strip()
    country = row.get("Country","").strip()
    tikr_by_exchange[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "sector":sector,"country":country,"ex_raw":ex_raw
    }
print(f"Colonna market cap trovata e usata: {mktcap_col_usata}")

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

    # Calcola candidati — escludi ETF/fondi, ordina per mkt_cap
    candidati = []
    for t, info in tikr.items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]): continue
        candidati.append((t, mc))
    candidati.sort(key=lambda x: x[1], reverse=True)

    excl_count = len(tikr) - len([t for t in tikr if not is_excluded(tikr[t]["company"])])
    print(f"  Nel TIKR: {len(tikr)} — esclusi ETF/fondi: {excl_count}")

    # Verifica Leeway in ordine di mkt_cap decrescente: se un candidato non
    # ha prezzo, si scarta e si passa al prossimo per mkt_cap — backfill
    # automatico, il conteggio finale resta sempre top_n (se ci sono
    # abbastanza candidati con prezzo disponibile).
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
        print(f"  Scartati per mancanza prezzo Leeway: {len(esclusi_no_leeway)} (es. {esclusi_no_leeway[:10]})")

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

    # Aggiorna mkt_cap in fundamentals — upsert, non PATCH (una PATCH
    # non tocca righe non ancora esistenti per titoli nuovi in universo)
    mkt_updates = [{"ticker": t, "exchange": exchange, "mkt_cap": mc} for t, mc in eligible if mc]
    for i in range(0, len(mkt_updates), 100):
        requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals",
            headers=headers_up, json=mkt_updates[i:i+100])

    # Reset in_universe=false per exchange
    requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
        headers=headers_up,
        params={"exchange":f"eq.{exchange}"},
        json={"in_universe": False})

    # Set in_universe=true A BLOCCHI (non un titolo alla volta): una PATCH
    # con filtro ticker=in.(...) aggiorna centinaia di righe in una sola
    # chiamata, molto più affidabile delle PATCH singole che causavano
    # US=1917 invece di 2000 per richieste individuali fallite in silenzio.
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

    # ── RICONCILIAZIONE: verifica REALE riga per riga, non fidarsi del
    # solo HTTP 200 del blocco (un blocco puo' "riuscire" anche se solo
    # alcuni titoli al suo interno erano gia' presenti come riga in stocks).
    # Confronta l'insieme atteso con quello reale e corregge chi manca,
    # uno alla volta finche' non collima esattamente.
    r_check = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exchange}", "limit": "10000"})
    actual_set = set(row["ticker"] for row in r_check.json()) if isinstance(r_check.json(), list) else set()
    missing = [t for t in eligible_tickers if t not in actual_set]
    if missing:
        print(f"  Riconciliazione: {len(missing)} titoli mancanti dopo i blocchi, correggo uno per uno...")
        for t in missing:
            # Se la riga non esiste affatto in stocks, creala ora
            rex = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker", "ticker": f"eq.{t}", "exchange": f"eq.{exchange}"})
            if not (isinstance(rex.json(), list) and rex.json()):
                info = tikr[t]
                country = info.get("country") or COUNTRY_DEFAULT[exchange]
                requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_ins, json=[{
                    "ticker": t, "exchange": exchange, "company": info["company"],
                    "sector": info["sector"], "country": country,
                    "flag": FLAG_MAP.get(country, FLAG_MAP[COUNTRY_DEFAULT[exchange]]),
                    "currency": CURRENCY_MAP[exchange], "in_universe": False,
                    "primary_exchange": info["ex_raw"],
                }])
            rp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
                params={"ticker": f"eq.{t}", "exchange": f"eq.{exchange}"},
                json={"in_universe": True})
            if rp.status_code in (200, 204):
                ok += 1
            else:
                print(f"    ANCORA FALLITO {t}: {rp.status_code} {rp.text[:120]}")
        # riverifica dopo la riconciliazione
        r_check2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exchange}", "limit": "10000"})
        actual_set2 = set(row["ticker"] for row in r_check2.json()) if isinstance(r_check2.json(), list) else set()
        still_missing = [t for t in eligible_tickers if t not in actual_set2]
        if still_missing:
            print(f"  ANCORA MANCANTI dopo riconciliazione ({len(still_missing)}): {still_missing}")
        else:
            print(f"  Riconciliazione completata: tutti i {len(eligible_tickers)} titoli sono ora in_universe=true")
        ok = len(actual_set2)
    else:
        print(f"  Riconciliazione: nessun gap, {len(eligible_tickers)}/{len(eligible_tickers)} confermati")

    total_na += ok
    print(f"  in_universe=true: {ok}/{len(eligible_tickers)}")
    print()

print(f"=== TOTALE NA IN UNIVERSE: {total_na} ===")
print(f"Atteso: US=3000 + TSX=400 = 3400")

# Verifica finale REALE dal DB (count=exact), non il conteggio dei chunk
print("\nVerifica finale dal DB:")
headers_count = {**headers_r, "Prefer": "count=exact"}
for exch in ["US", "TSX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "in_universe": "eq.true",
                "exchange": f"eq.{exch}", "limit": "1"})
    print(f"  {exch} in_universe (DB): {r.headers.get('content-range')}")
