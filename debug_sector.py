import os, requests, random
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

print("=== Data piu' recente per mercato + copertura a campione (20 titoli) ===\n")
for ex in ALL_RANKED:
    # Data piu' recente in assoluto per questo mercato (query veloce, no count)
    rd = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    newest = rd.json()
    newest_date = newest[0]["date"] if newest else "NESSUN DATO"

    # Campione di 20 ticker random dall'universo di questo mercato
    ru = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000"})
    universe = [s["ticker"] for s in ru.json()]
    if not universe:
        print(f"  {ex}: universo vuoto")
        continue
    sample = random.sample(universe, min(20, len(universe)))

    covered = 0
    for tk in sample:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","limit":"1"})
        if rp.json():
            covered += 1

    pct = round(covered/len(sample)*100)
    print(f"  {ex}: piu' recente={newest_date} | copertura campione={covered}/{len(sample)} ({pct}%)")
