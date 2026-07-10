import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
for row in reader:
    if row.get("Ticker","").strip() == "8309":
        print("Company:", row.get("Company Name"))
        for k in ["EPS (GAAP) (FY 2025)","Mean EPS (GAAP) (FY 2026)",
                   "Mean EPS (GAAP) (FY 2027)","Mean EPS (GAAP) (FY 2028)",
                   "EPS Normalized (FY 2025)","Mean EPS Normalized (FY 2026)",
                   "Mean EPS Normalized (FY 2027)","Mean EPS Normalized (FY 2028)"]:
            print(f"  {k}: {row.get(k)!r}")
        break
else:
    print("8309 non trovato")

# fiscal year end
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader2 = csv.DictReader(io.StringIO(r2.text))
for row in reader2:
    if row.get("ticker","").strip() == "8309":
        print("fiscal_year_end.csv:", row)
        break
else:
    print("8309 non in fiscal_year_end.csv")
