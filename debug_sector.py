import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,sector,value_score,growth_score,combined_rank","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA:", r.json())

nvda_sector = r.json()[0].get("sector") if r.json() else None
print(f"\nSettore NVDA: '{nvda_sector}'")

if nvda_sector:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,value_score","exchange":"in.(US,TSX)","sector":f"eq.{nvda_sector}","value_score":"not.is.null","limit":"5"})
    print(f"\nAltri titoli US/TSX nello stesso settore con value_score non nullo:", r2.json())
