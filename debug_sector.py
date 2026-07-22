import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,change1d,value_score,growth_score,combined_rank","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL.US:", r.json())

# Campione NA per Best Score
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,combined_rank","exchange":"in.(US,TSX)","combined_rank":"not.is.null","limit":"5"})
print("\nCampione con Best Score popolato (US/TSX):", r2.json())

r3 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers={**headers_r,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"in.(US,TSX)","combined_rank":"not.is.null","limit":"1"})
print("\nQuanti in US+TSX hanno Best Score:", r3.headers.get("content-range"))
