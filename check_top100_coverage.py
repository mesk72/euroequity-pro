import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r_fy = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r_fy.text))
have = set()
for row in reader:
    if row["fiscal_month"] not in ("0",""):
        have.add((row["ticker"], row["exchange"]))

for exch, n in [("SGX", 100), ("SEHK", 100)]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,mkt_cap","exchange":f"eq.{exch}","mkt_cap":"not.is.null",
                "order":"mkt_cap.desc","limit":str(n)})
    top = r.json()
    covered = sum(1 for t in top if (t["ticker"], exch) in have)
    print(f"{exch} — primi {len(top)} per mkt cap: {covered} con dato fiscale")
    missing_top = [t["ticker"] for t in top if (t["ticker"], exch) not in have]
    print(f"  mancanti tra i top: {missing_top[:15]}")
