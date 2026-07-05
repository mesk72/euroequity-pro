import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

tickers = ["MU", "MRVL"]

for t in tickers:
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "*", "ticker": f"eq.{t}", "exchange": "eq.US"})
    data = r.json()
    print(f"=== {t} ===")
    if isinstance(data, list) and data:
        row = data[0]
        for k in ["price", "beta", "ke", "pe_forward", "eps_ntm_dcf",
                   "implied_growth_10y", "eps_fwd24", "eps_fwd36",
                   "eps_growth_12_24m", "eps_growth_24_36m", "eps_cagr_2y",
                   "eps_growth", "value_score", "growth_score"]:
            print(f"  {k}: {row.get(k)}")
    else:
        print("  NESSUNA RIGA TROVATA")
    print()
