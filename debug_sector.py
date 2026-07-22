import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for ex in ["US", "TSX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,value_score,growth_score,combined_rank","exchange":f"eq.{ex}","limit":"5"})
    print(f"=== {ex} campione ===")
    for row in r.json():
        print(" ", row)

# Controlla anche AAPL specificamente
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,value_score,growth_score,combined_rank","ticker":"eq.AAPL","exchange":"eq.US"})
print("\nAAPL.US:", r2.json())
