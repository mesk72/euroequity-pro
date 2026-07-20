import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

sectors = ["Information Technology", "Financials", "Healthcare", "Consumer Discretionary",
           "Industrials", "Communication Services", "Consumer Staples", "Energy",
           "Materials", "Utilities", "Real Estate"]

print("=== VERO conteggio Screener US (exchange=US esatto, in_universe=true) ===\n")
for sec in sectors:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true"})
    cr = r.headers.get("content-range", "")
    count = cr.split("/")[-1] if "/" in cr else "?"
    print(f"  {sec}: {count}")
