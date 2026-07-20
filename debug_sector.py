import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,sector","ticker":"eq.C","exchange":"eq.US"})
print("Citigroup sector esatto:", r.json())

for s in ["Financials", "Financial", "Financial Services"]:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":"in.(US,TSX)","sector":f"eq.{s}"})
    cr = r2.headers.get("content-range", "")
    print(f"Conteggio stocks per sector='{s}' (US+TSX): {cr}")
