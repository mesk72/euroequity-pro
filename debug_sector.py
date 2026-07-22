import os, requests, random, sys
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

print("=== Data piu' recente + copertura a campione (8 titoli) ===", flush=True)
for ex in ALL_RANKED:
    rd = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    newest = rd.json()
    newest_date = newest[0]["date"] if newest else "NESSUN DATO"

    ru = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000"})
    universe = [s["ticker"] for s in ru.json()]
    if not universe:
        print(f"  {ex}: universo vuoto", flush=True)
        continue
    sample = random.sample(universe, min(8, len(universe)))

    covered = 0
    for tk in sample:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","limit":"1"})
        if rp.json():
            covered += 1

    pct = round(covered/len(sample)*100)
    print(f"  {ex}: piu_recente={newest_date} copertura={covered}/{len(sample)} ({pct}%)", flush=True)
