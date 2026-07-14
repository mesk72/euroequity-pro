import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

# Verifica se esiste gia'
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"eq.BSP","exchange":"eq.US"})
print("BSP gia' presente?", r.json())

stock_row = {
    "ticker": "BSP", "exchange": "US", "company": "Bending Spoons S.p.A.",
    "sector": "Information Technology", "country": "Italy", "in_universe": True,
}
r2 = requests.post(f"{SUPABASE_URL}/rest/v1/stocks?on_conflict=ticker,exchange",
    headers=headers_up, json=[stock_row], timeout=20)
print("Insert stocks:", r2.status_code, r2.text[:200])

fund_row = {
    "ticker": "BSP", "exchange": "US", "mkt_cap": 25700.0, "price": 40.50,
}
r3 = requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals?on_conflict=ticker,exchange",
    headers=headers_up, json=[fund_row], timeout=20)
print("Insert fundamentals (placeholder mkt_cap/price):", r3.status_code, r3.text[:200])
