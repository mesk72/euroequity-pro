import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"100"})
tickers = [row["ticker"] for row in r.json()]
dates = {}
for t in tickers:
    rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"1"})
    d = rr.json()
    date_val = d[0]["date"] if d else "VUOTO"
    dates[date_val] = dates.get(date_val, 0) + 1
print("Primi 100 titoli US, dopo il test:")
for d, c in sorted(dates.items(), reverse=True):
    print(f"  {d}: {c}")
