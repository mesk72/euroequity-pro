import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ex in ["US", "TSX"]:
    for sector in ["Financials", "Materials"]:
        offset = 0
        found = []
        while True:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
                params={"select":"ticker","exchange":f"eq.{ex}","sector":f"eq.{sector}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
            batch = r.json()
            if not isinstance(batch,list) or not batch: break
            for s in batch:
                r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
                    params={"select":"ticker,change1d,price","ticker":f"eq.{s['ticker']}","exchange":f"eq.{ex}"})
                d = r2.json()
                if d and d[0].get("change1d") is not None and abs(d[0]["change1d"]) > 0.4:
                    found.append((ex, sector, d[0]))
            offset += 1000
            if len(batch) < 1000: break
        for f in found:
            print(f)
