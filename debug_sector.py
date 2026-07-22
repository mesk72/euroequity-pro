import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

print("=== Copertura per mercato ===")
total_tickers_with_data = 0
total_universe = 0
for ex in ALL_RANKED:
    # Quanti ticker nell'universo per questo mercato
    ru = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers={**headers_r,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1"})
    universe_count = int(ru.headers.get("content-range","0/0").split("/")[-1])

    # Ticker distinti con almeno una riga prezzo per questo mercato
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"1000"})
    distinct_with_data = len(set(row["ticker"] for row in rp.json())) if rp.status_code==200 else 0

    total_universe += universe_count
    total_tickers_with_data += distinct_with_data
    print(f"  {ex}: universo={universe_count}, con_dati(campione)={distinct_with_data}")

print(f"\nTotale universo: {total_universe}")

# Campione di profondita' storica su alcuni titoli specifici
print("\n=== Profondita' storica campione ===")
for ticker, exchange in [("AAPL","US"),("SAP","XETRA"),("7203","TSE"),("NOVO B","CPSE")]:
    r1 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.asc","limit":"1"})
    oldest = r1.json()
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    newest = r2.json()
    print(f"  {ticker}.{exchange}: da {oldest} a {newest}")
