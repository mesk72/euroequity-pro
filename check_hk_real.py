import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Prezzi HK - campione di 30
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.SEHK","in_universe":"eq.true","limit":"30"})
tickers = [row["ticker"] for row in r.json()]
dates = {}
for t in tickers:
    rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.SEHK","order":"date.desc","limit":"1"})
    d = rr.json()
    date_val = d[0]["date"] if d else "VUOTO"
    dates[date_val] = dates.get(date_val, 0) + 1
print("Prezzi HK, campione 30:")
for d, c in sorted(dates.items(), reverse=True):
    print(f"  {d}: {c}")

# Fiscal year HK
import csv, io
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
hk_rows = [row for row in reader if row["exchange"]=="SEHK"]
valid = sum(1 for row in hk_rows if row["fiscal_month"] not in ("0",""))
print(f"\nFiscal year HK: {valid}/{len(hk_rows)} validi")
