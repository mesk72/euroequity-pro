import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
targets = ["D05","7203","700","BHP"]  # DBS(banca), Toyota, Tencent, BHP
for row in reader:
    if row.get("Ticker","").strip() in targets:
        t = row.get("Ticker")
        print(f"{t} ({row.get('Company Name')}, {row.get('Sector')}):")
        print(f"  Rev FY25={row.get('Rev (FY 2025)')!r}  Rev FY26={row.get('Mean Rev (FY 2026)')!r}  Rev FY27={row.get('Mean Rev (FY 2027)')!r}")
        print(f"  EPS Norm FY25={row.get('EPS Normalized (FY 2025)')!r}  EPS GAAP FY25={row.get('EPS (GAAP) (FY 2025)')!r}")
