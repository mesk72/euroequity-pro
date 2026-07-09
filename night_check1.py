import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
checks = [
    ("Website US", "stocks", {"exchange":"eq.US","in_universe":"eq.true","website":"not.is.null"}),
    ("Beta US", "fundamentals", {"exchange":"eq.US","beta":"not.is.null"}),
    ("DCF US", "fundamentals", {"exchange":"eq.US","eps_ntm_dcf":"not.is.null"}),
    ("Website KRX", "stocks", {"exchange":"eq.KRX","in_universe":"eq.true","website":"not.is.null"}),
    ("Website SGX", "stocks", {"exchange":"eq.SGX","in_universe":"eq.true","website":"not.is.null"}),
]
for label, table, params in checks:
    p = {"select":"ticker", "limit":"1", **params}
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_r, params=p)
    print(f"{label}: {r.headers.get('content-range')}")
