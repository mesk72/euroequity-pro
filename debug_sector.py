import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

sectors = ["Information Technology", "Financials", "Healthcare"]

# Tutti i fundamentals US con mkt_cap (indipendentemente da implied_growth)
fund_all_cap = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,implied_growth_10y","exchange":"eq.US","mkt_cap":"not.is.null",
                 "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    fund_all_cap.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

fund_map = {f["ticker"]: f for f in fund_all_cap}

for sec in sectors:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true","limit":"1000"})
    sector_tickers = [s["ticker"] for s in r2.json()]

    total_cap = 0.0
    covered_cap = 0.0
    for t in sector_tickers:
        f = fund_map.get(t)
        if f:
            cap = f.get("mkt_cap") or 0
            total_cap += cap
            if f.get("implied_growth_10y") is not None:
                covered_cap += cap

    pct = round(covered_cap/total_cap*100, 1) if total_cap > 0 else 0
    print(f"{sec}: mkt cap totale ${total_cap/1000:.1f}B | mkt cap coperto ${covered_cap/1000:.1f}B | copertura per capitalizzazione: {pct}%")
