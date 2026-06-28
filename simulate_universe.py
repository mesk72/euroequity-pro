import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

MIN_PRICE_DATE = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]
EXCLUDE_NAMES = [
    "ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    name = (company or "").upper()
    return any(kw in name for kw in EXCLUDE_NAMES)

def load_exchange(exchange):
    stocks = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,company,sector,mkt_cap,in_universe",
                    "exchange": f"eq.{exchange}",
                    "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    return stocks

def get_tickers_with_prices(exchange):
    tickers = set()
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "ticker", "exchange": f"eq.{exchange}",
                    "date": f"gte.{MIN_PRICE_DATE}",
                    "order": "ticker.asc", "limit": "2000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        for row in batch: tickers.add(row["ticker"])
        offset += 2000
        if len(batch) < 2000: break
    return tickers

print(f"MIN_PRICE_DATE: {MIN_PRICE_DATE}")
print()

# DEBUG: verifica cosa c'e nel DB per ogni exchange
print("=== DEBUG ===")
for ex in ["LSE","XETRA","PA","MIL","US","TSX"]:
    stocks = load_exchange(ex)
    with_price = get_tickers_with_prices(ex)
    
    # Statistiche mkt_cap
    has_mktcap = [s for s in stocks if s.get("mkt_cap") and s.get("mkt_cap") > 0]
    above_500 = [s for s in stocks if (s.get("mkt_cap") or 0) >= 500]
    not_excluded = [s for s in stocks if not is_excluded(s.get("company",""), s.get("sector",""))]
    eligible = [s for s in stocks
                if not is_excluded(s.get("company",""), s.get("sector",""))
                and (s.get("mkt_cap") or 0) >= 500]
    
    print(f"{ex}:")
    print(f"  totale nel DB: {len(stocks)}")
    print(f"  con mkt_cap > 0: {len(has_mktcap)}")
    print(f"  con mkt_cap >= 500: {len(above_500)}")
    print(f"  non esclusi (ETF/fondi): {len(not_excluded)}")
    print(f"  eligible (non esclusi + >=500M): {len(eligible)}")
    print(f"  con prezzi recenti: {len(with_price)}")
    
    # Mostra 3 esempi
    if stocks:
        for s in stocks[:3]:
            print(f"  es: {s['ticker']} mkt_cap={s.get('mkt_cap')} sector={s.get('sector')} company={s.get('company','')[:30]}")
    print()

print("=== NESSUNA MODIFICA AL DB ===")
