import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.TSE","in_universe":"eq.true","limit":"15"})
sample = [s["ticker"] for s in r.json()]

for tk in sample:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"price,change1d","ticker":f"eq.{tk}","exchange":"eq.TSE"})
    d = r2.json()
    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":"eq.TSE","order":"date.desc","limit":"1"})
    p = r3.json()
    fund_price = d[0]["price"] if d else None
    real_price = p[0]["adj_close"] if p else None
    match = "OK" if fund_price and real_price and abs(fund_price - real_price) < 0.01 else "MISMATCH"
    print(f"{tk}: fundamentals.price={fund_price}, prices_eod reale={real_price} [{match}]")
