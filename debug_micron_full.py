import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== RIGA GREZZA TIKR PER MU ===")
r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
for row in reader:
    if row.get("Ticker", "").strip() == "MU":
        for k in ["Ticker", "Exchange", "Market",
                  "EPS Normalized (FY 2025)",
                  "Mean EPS Normalized (FY 2026)",
                  "Mean EPS Normalized (FY 2027)",
                  "Mean EPS Normalized (FY 2028)",
                  "Mean EPS Normalized (FY 2029)",
                  "Mean EPS Normalized (FY 2030)",
                  "Mean EPS (GAAP) (FY 2029)",
                  "Mean EPS (GAAP) (FY 2030)"]:
            print(f"  {k}: {row.get(k)}")
        break

print("\n=== VALORI SALVATI IN FUNDAMENTALS PER MU ===")
r2 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
    params={"select": "*", "ticker": "eq.MU", "exchange": "eq.US"})
data = r2.json()
if isinstance(data, list) and data:
    row = data[0]
    for k in ["price", "beta", "ke", "eps_ntm_dcf", "implied_growth_10y",
              "eps_fwd24", "eps_fwd36", "eps_growth_12_24m",
              "eps_growth_24_36m", "eps_cagr_2y"]:
        print(f"  {k}: {row.get(k)}")
