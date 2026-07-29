import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

exchanges = ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
             "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
for ex in exchanges:
    # universo per questo exchange
    us_r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"3000"})
    universe = set(r["ticker"] for r in us_r.json())
    if not universe: continue
    lp_r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"3000"})
    have = set(r["ticker"] for r in lp_r.json())
    missing = sorted(universe - have)
    if missing:
        print(f"{ex}: {len(missing)} assenti -> {missing[:50]}")
