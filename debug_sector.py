import os, requests, random
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

SAMPLE_SIZE = 15
all_max_dates = []

print("=== Campione per mercato: quanti hanno dati, a che data ===\n")
for ex in ALL_RANKED:
    ru = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000"})
    universe = [s["ticker"] for s in ru.json()]
    if not universe:
        print(f"  {ex}: universo vuoto")
        continue

    sample = random.sample(universe, min(SAMPLE_SIZE, len(universe)))
    with_data = 0
    max_dates_this_market = []
    for tk in sample:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
        rows = rp.json()
        if rows:
            with_data += 1
            max_dates_this_market.append(rows[0]["date"])
            all_max_dates.append(rows[0]["date"])

    pct = round(with_data/len(sample)*100)
    latest = max(max_dates_this_market) if max_dates_this_market else "N/A"
    print(f"  {ex}: {with_data}/{len(sample)} campione con dati ({pct}%), universo={len(universe)}, data piu' recente nel campione={latest}")

print(f"\n=== Data piu' recente in assoluto trovata: {max(all_max_dates) if all_max_dates else 'N/A'} ===")
