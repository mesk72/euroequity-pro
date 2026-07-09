import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
for row in reader:
    if row.get("Ticker","").strip() == "D05":
        for k in ["Rev (FY 2025)","Mean Rev (FY 2026)","Mean Rev (FY 2027)","Mean Rev (FY 2028)",
                   "EPS Normalized (FY 2025)","Mean EPS Normalized (FY 2026)","Mean EPS Normalized (FY 2027)","Mean EPS Normalized (FY 2028)"]:
            print(f"  {k}: {row.get(k)!r}")
        break

# controlla get_fy_month per D05.SGX
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader2 = csv.DictReader(io.StringIO(r2.text))
found = False
for row in reader2:
    if row.get("ticker","").strip() == "D05":
        print(f"  fiscal_year_end.csv D05: {row}")
        found = True
if not found:
    print("  D05 NON presente in fiscal_year_end.csv -> usa default mese 12")
