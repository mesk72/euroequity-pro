import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

samples = [("7203","TSE","Toyota"),("700","SEHK","Tencent"),("BHP","ASX","BHP"),
           ("A005930","KRX","Samsung"),("D05","SGX","DBS")]
for t, ex, name in samples:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mkt_cap,updated_at" if False else "ticker,exchange,mkt_cap","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    print(f"{name} ({t}.{ex}): {r.json()}")

# quanti APAC in_universe hanno mkt_cap NULL vs popolato
for ex in ["TSE","SEHK","ASX","KRX","SGX"]:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"10"})
    tickers = [s["ticker"] for s in r2.json()] if isinstance(r2.json(),list) else []
    nulls = 0
    for t in tickers:
        rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"mkt_cap","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
        d = rf.json()
        if not (isinstance(d,list) and d and d[0].get("mkt_cap")):
            nulls += 1
    print(f"{ex}: {nulls}/{len(tickers)} campione con mkt_cap NULL")
