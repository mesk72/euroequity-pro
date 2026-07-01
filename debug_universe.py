import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EX_MAP_EU = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","SWX":"SWX","LSE":"LSE","CPSE":"CPSE",
    "HMSE":"OM","XSAT":"OM","OB":"OB","OTCNO":"OB",
    "XATH":"GR","ATH":"GR",
}

EX_MAP_APAC = {
    "TSE":"TSE","JPX":"TSE",
    "SEHK":"SEHK","HKEX":"SEHK",
    "ASX":"ASX",
    "KRX":"KRX","KOSPI":"KRX","KOSDAQ":"KRX",
    "SGX":"SGX",
}

ALWAYS_EXCLUDE = [
    " ETF"," ETP"," ETC ","UCITS",
    "GOLD SHARES","SILVER SHARES","GOLD TRUST","SILVER TRUST",
    "GOLD MINISHARES","PHYSICAL GOLD","PHYSICAL SILVER","PHYSICAL METALS",
    "COVERED CALL FUND","MONEY MARKET FUND","SAVINGS FUND",
    "SAVINGS ACCOUNT FUND","CASH FUND","CASH MANAGEMENT FUND",
    "DYNAMIC OVERWRITE FUND","PREMIUM YIELD FUND",
    "COMMODITY INDEX TRACKING","AGRICULTURE FUND",
    "HIGH INTEREST SAVINGS","3X LEVERAGED","2X LEVERAGED","-1X LEVERAGED",
    "EXCHANGE TRADED NOTE","EXCHANGE-TRADED NOTE",
    "XTRACKERS","LYXOR","VANGUARD ETF","AMUNDI ETF",
    "SPDR ETF","SPDR GOLD","SPDR SILVER",
    "ISHARES GOLD","ISHARES SILVER","ISHARES PHYSICAL",
    "WISDOMTREE ETF","VANECK ETF","INDEX FUND","BOND FUND",
    "MUTUAL FUND","MUTUALFUND",
]

def is_excluded(company):
    name = (company or "").upper()
    for kw in ALWAYS_EXCLUDE:
        if kw in name: return True
    return False

# EU
print("=== EUROPA ===")
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
eu_excluded = []
eu_by_exchange = {}
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP_EU.get(ex_raw, ex_raw)
    company = row.get("Company Name","").strip()
    if not ticker: continue
    excl = is_excluded(company)
    if excl:
        eu_excluded.append((ticker, exchange, company))
    eu_by_exchange[exchange] = eu_by_exchange.get(exchange, {"total":0,"excluded":0})
    eu_by_exchange[exchange]["total"] += 1
    if excl: eu_by_exchange[exchange]["excluded"] += 1

print(f"Totale EU: {sum(v['total'] for v in eu_by_exchange.values())}")
print(f"Esclusi EU: {len(eu_excluded)}")
for ex in sorted(eu_by_exchange):
    v = eu_by_exchange[ex]
    print(f"  {ex:<8} totale={v['total']:>5} esclusi={v['excluded']:>4}")
print("\nLista esclusi EU:")
for t, ex, c in sorted(eu_excluded):
    print(f"  {t:<15} {ex:<8} {c}")

# APAC — legge da stocks DB (non abbiamo file TIKR APAC)
print("\n=== APAC (da DB stocks) ===")
for exchange in ["TSE","SEHK","ASX","KRX","SGX"]:
    stocks = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,company,in_universe",
                    "exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        stocks.extend(batch)
        offset += 1000
        if len(batch)<1000: break
    excl = [s for s in stocks if is_excluded(s.get("company",""))]
    print(f"  {exchange}: totale={len(stocks)} esclusi={len(excl)}")
    for s in excl:
        print(f"    {s['ticker']:<15} {s.get('company','')}")
