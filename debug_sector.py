import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

sectors = ["Information Technology", "Financials", "Healthcare"]

fund_all = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,value_score","exchange":"eq.US","mkt_cap":"not.is.null","value_score":"not.is.null",
                 "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    fund_all.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

fund_map = {f["ticker"]: f for f in fund_all}

for sec in sectors:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true","limit":"1000"})
    sector_tickers = [s["ticker"] for s in r2.json()]

    wsum = 0.0
    capsum = 0.0
    count = 0
    for t in sector_tickers:
        f = fund_map.get(t)
        if f:
            cap = f["mkt_cap"]
            wsum += f["value_score"] * cap
            capsum += cap
            count += 1

    avg = round(wsum/capsum, 1) if capsum > 0 else None
    print(f"{sec}: Value Score medio pesato = {avg} (su {count} titoli, ${capsum/1000:.1f}B)")
