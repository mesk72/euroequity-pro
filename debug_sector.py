import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

sectors = ["Information Technology", "Financials", "Healthcare"]

for sec in sectors:
    # Totale vero (Screener US)
    r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true"})
    total = r1.headers.get("content-range","").split("/")[-1]

    # Quanti di questi hanno anche implied_growth_10y e mkt_cap validi
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true","limit":"1000"})
    tickers = [s["ticker"] for s in r2.json()]

    count_with_data = 0
    for t in tickers:
        rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"mkt_cap,implied_growth_10y","ticker":f"eq.{t}","exchange":"eq.US"})
        d = rf.json()
        if d and d[0].get("mkt_cap") and d[0].get("implied_growth_10y") is not None:
            count_with_data += 1

    print(f"{sec}: {count_with_data} su {total} hanno implied growth calcolabile ({round(count_with_data/int(total)*100,1)}% copertura)")
