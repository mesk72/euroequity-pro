import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EXCLUDE_NAMES = [
    "ETF","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS",
    "LYXOR","AMUNDI ETF","INVESCO","SPDR","WISDOMTREE","VANECK",
    "BLACKROCK","INDEX FUND","TRACKER","WARRANT","CERTIFICATE",
    "ETP","ETC","STRUCTURED","NOTES","BOND FUND",
]
EXCLUDE_SECTORS = ["71","72","73","74","75","76","77"]

def is_excluded(company, sector):
    if sector in EXCLUDE_SECTORS: return True
    return any(kw in (company or "").upper() for kw in EXCLUDE_NAMES)

for exchange in ["US","LSE"]:
    # Carica tutti i titoli con mkt_cap da fundamentals
    fund = {}
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,mkt_cap","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: fund[s["ticker"]] = s.get("mkt_cap") or 0
        offset += 1000
        if len(batch)<1000: break

    # Carica stocks per esclusioni
    stocks = {}
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,company,sector","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch: stocks[s["ticker"]] = s
        offset += 1000
        if len(batch)<1000: break

    total = len(stocks)
    no_mktcap = sum(1 for t in stocks if fund.get(t,0) == 0)
    excluded = sum(1 for t,s in stocks.items()
                   if is_excluded(s.get("company",""), s.get("sector","")))
    above_500 = sum(1 for t in stocks
                    if not is_excluded(stocks[t].get("company",""), stocks[t].get("sector",""))
                    and fund.get(t,0) >= 500)
    not_excluded = sum(1 for t,s in stocks.items()
                       if not is_excluded(s.get("company",""), s.get("sector","")))

    print(f"\n{exchange}:")
    print(f"  Totale nel DB: {total}")
    print(f"  Con mkt_cap > 0: {sum(1 for t in stocks if fund.get(t,0)>0)}")
    print(f"  Con mkt_cap = 0: {no_mktcap}")
    print(f"  Esclusi (ETF/fondi): {excluded}")
    print(f"  Non esclusi: {not_excluded}")
    print(f"  Non esclusi con mkt_cap >= 500M: {above_500}")
    print(f"  Non esclusi con mkt_cap > 0: {sum(1 for t,s in stocks.items() if not is_excluded(s.get('company',''),s.get('sector','')) and fund.get(t,0)>0)}")
