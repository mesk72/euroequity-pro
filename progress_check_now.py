import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ex in ["ASX","SEHK","BR","TSE"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"30"})
    tickers = [row["ticker"] for row in r.json()]
    dates = {}
    for t in tickers:
        rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
        d = rr.json()
        dv = d[0]["date"] if d else "VUOTO"
        dates[dv] = dates.get(dv, 0) + 1
    freshest = max(dates.keys())
    print(f"{ex}: {dates.get(freshest,0)}/{len(tickers)} a {freshest} — {dates}")

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,change1d","ticker":"eq.JPM","exchange":"eq.US"})
print("JPM fundamentals ora:", r2.json())
