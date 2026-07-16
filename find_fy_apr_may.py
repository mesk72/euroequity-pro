import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for month, name in [(4,"aprile"),(5,"maggio")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,fiscal_month,mkt_cap","exchange":"eq.US","fiscal_month":f"eq.{month}",
                 "mkt_cap":"gte.10000","order":"mkt_cap.desc","limit":"5"})
    print(f"Fiscal year fine {name} (mese={month}):")
    for row in r.json():
        print(f"  {row}")
