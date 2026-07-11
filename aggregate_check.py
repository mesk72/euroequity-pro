import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def count_fresh(exchange, universe_exchanges, min_date):
    # universo totale
    total = set()
    for ex in universe_exchanges:
        offset = 0
        while True:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
                params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
            batch = r.json()
            if not isinstance(batch,list) or not batch: break
            total.update((s["ticker"], s["exchange"]) for s in batch)
            offset += 1000
            if len(batch) < 1000: break
    # freschi
    fresh = set()
    for ex in universe_exchanges:
        offset = 0
        while True:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
                params={"select":"ticker,exchange","exchange":f"eq.{ex}","date":f"gte.{min_date}","limit":"1000","offset":str(offset)})
            batch = r.json()
            if not isinstance(batch,list) or not batch: break
            fresh.update((row["ticker"], row["exchange"]) for row in batch)
            offset += 1000
            if len(batch) < 1000: break
    return len(total), len(fresh)

for label, exchanges, min_date in [
    ("US+CA", ["US","TSX"], "2026-07-08"),
    ("EU", ["MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS"], "2026-07-08"),
    ("APAC", ["TSE","SEHK","ASX","KRX","SGX"], "2026-07-08"),
]:
    tot, fresh = count_fresh(label, exchanges, min_date)
    print(f"{label}: {fresh}/{tot} freschi (>= 8 luglio) = {100*fresh/tot:.0f}%")
