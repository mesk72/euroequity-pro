import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== daily_log per il 28/7 ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/daily_log", headers=headers_r,
    params={"select":"*","run_date":"eq.2026-07-28","order":"market.asc"})
for row in r.json():
    print(row)

print("\n=== conteggio effettivo titoli in_universe per exchange, con prezzo al 28/7 ===")
for label, exchanges in [("EU", ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]),
                          ("NA", ["US","TSX"])]:
    total_universe = 0
    total_priced_28 = 0
    for ex in exchanges:
        rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"1"})
        # count via Prefer count
        rc = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r | {"Prefer":"count=exact"},
            params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"1"})
        cr = rc.headers.get("content-range","0/0")
        cnt = int(cr.split("/")[-1]) if "/" in cr else 0
        total_universe += cnt
    print(f"{label}: universo totale in_universe=true -> {total_universe}")
