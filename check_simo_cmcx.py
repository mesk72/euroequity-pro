import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"eq.SIMO","exchange":"eq.XETRA"})
print("SIMO XETRA stocks:", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,mom1w,mom1m,pe_trailing","ticker":"eq.SIMO","exchange":"eq.XETRA"})
print("SIMO XETRA fundamentals:", r2.json())

r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"eq.CMCX","exchange":"eq.LSE"})
print("\nCMCX LSE stocks:", r3.json())
r4 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,pe_trailing,mom1w,mom1m","ticker":"eq.CMCX","exchange":"eq.LSE"})
print("CMCX LSE fundamentals:", r4.json())
