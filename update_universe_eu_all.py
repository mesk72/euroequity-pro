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

SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE", "ROG": "RO.SW",
}
LEEWAY_SUFFIX = {
    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":    ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":    ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":    ".IR",    "GR":    ".AT",
    "SWX":   ".SW",    "OM":    ".ST",     "OB":   ".OL",
    "CPSE":  ".CO",
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange in ("CPSE", "OM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
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

EX_MAP = {
    # Italia
    "BIT":"MIL",
    # UK (AIM escluso: mercato alternativo, non va fuso con LSE)
    "LSE":"LSE",
    # Germania
    "XTRA":"XETRA","HMSE":"XETRA","DB":"XETRA","MUN":"XETRA","DUSE":"XETRA",
    # Francia
    "ENXTPA":"PA",
    # Svezia (NGM escluso: mercato alternativo, non va fuso con OM)
    "OM":"OM","XSAT":"OM",
    # Svizzera
    "SWX":"SWX","BRSE":"SWX",
    # Olanda
    "ENXTAM":"AS",
    # Spagna
    "BME":"MC","BDM":"MC",
    # Belgio
    "ENXTBR":"BR",
    # Finlandia
    "HLSE":"HE",
    # Danimarca
    "CPSE":"CPSE",
    # Norvegia
    "OB":"OB","OTCNO":"OB",
    # Grecia
    "ATSE":"GR","XATH":"GR","ATH":"GR",
    # Austria
    "WBAG":"VI",
    # Irlanda
    "ISE":"IR",
    # Portogallo
    "ENXTLS":"LS",
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

# Criteri per exchange
# min_cap=400 → mkt_cap >= 400M
# top_n=100 → top 100 per mkt_cap
# min_cap=None, top_n=None → tutti
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

print("=== AGGIORNAMENTO IN_UNIVERSE TUTTE LE BORSE EU ===")
print()

# Carica TIKR EU
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

tikr_by_exchange = {ex:{} for ex in EXCHANGE_CRITERIA}
for row in reader:
    ticker  = row.get("Ticker","").strip()
    ex_raw  = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if not exchange or exchange not in tikr_by_exchange: continue
    company = row.get("Company Name","").strip()
    mktcap  = parse_mktcap(row.get("Last Mkt Cap",""))
    country = row.get("Country","").strip()
    sector  = row.get("Sector","").strip()
    tikr_by_exchange[exchange][ticker] = {
        "company":company,"mkt_cap":mktcap,
        "country":country,"sector":sector,"ex_raw":ex_raw
    }

total_eu = 0

for exchange, criteria in EXCHANGE_CRITERIA.items():
    # Salta MIL e LSE già aggiornati
    if exchange in ("MIL","LSE"):
        print(f"  {exchange:<8} SKIPPED (già aggiornato)")
        continue

    tikr = tikr_by_exchange[exchange]
    min_cap = criteria["min_cap"]
    top_n   = criteria["top_n"]

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

    # Calcola candidati — escludi ETF/fondi e sotto-soglia, ordina per mkt_cap
    candidati = []
    for t, info in tikr.items():
        mc = info["mkt_cap"] or 0
        if is_excluded(info["company"]): continue
        if min_cap and mc < min_cap: continue
        candidati.append((t, mc))
    candidati.sort(key=lambda x: x[1], reverse=True)

    # Verifica Leeway in ordine di mkt_cap decrescente. Per i mercati a
    # soglia (top_n=None) filtra tutti i candidati; per i mercati top-N
    # si ferma al target, scartando chi non ha prezzo e passando
    # automaticamente al prossimo per mkt_cap (backfill).
    eligible = []
    esclusi_no_leeway = []
    for t, mc in candidati:
        if top_n and len(eligible) >= top_n: break
        if ha_prezzo_su_leeway(t, exchange):
            eligible.append((t, mc))
        else:
            esclusi_no_leeway.append(t)
        time.sleep(0.1)

    eligible_tickers = [t for t,mc in eligible]
    if esclusi_no_leeway:
        print(f"  {exchange:<8} scartati senza prezzo Leeway: {len(esclusi_no_leeway)}")

    # Inserisci nuovi titoli
    new_stocks = []
    for t in eligible_tickers:
        if t not in stocks_db:
            info = tikr[t]
            new_stocks.append({
                "ticker": t, "exchange": exchange,
                "company": info["company"],
                "sector": info["sector"],
                "country": info.get("country") or COUNTRY_DEFAULT.get(exchange,""),
                "flag": FLAG_MAP.get(info.get("country") or COUNTRY_DEFAULT.get(exchange,""),"🏳️"),
                "currency": CURRENCY_MAP.get(exchange,"EUR"),
                "in_universe": False,
                "primary_exchange": info["ex_raw"],
            })

    if new_stocks:
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks",
            headers=headers_ins, json=new_stocks)
        print(f"  {exchange:<8} inseriti {len(new_stocks)} nuovi: HTTP {r2.status_code}")

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

    # Set in_universe=true A BLOCCHI (non un titolo alla volta)
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
            print(f"  FAIL blocco in_universe {exchange} {i}: {r2.status_code} {r2.text[:120]}")

    total_eu += ok
    print(f"  {exchange:<8} eligible={len(eligible_tickers):>5} in_universe=true={ok}")

# Ricontrolla dal DB MIL/LSE invece di un totale scritto a mano
for ex_mil_lse in ("MIL", "LSE"):
    r_check = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers={**headers_r, "Prefer": "count=exact"},
        params={"select": "ticker", "exchange": f"eq.{ex_mil_lse}", "in_universe": "eq.true", "limit": "1"})
    count = int(r_check.headers.get("content-range", "0/0").split("/")[-1])
    total_eu += count
    print(f"  {ex_mil_lse:<8} in_universe attuale (da DB): {count}")

print(f"\n=== TOTALE EU IN UNIVERSE: {total_eu} ===")
