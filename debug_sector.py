import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"})
data = r.json()
print("=== LOG ===")
if data:
    print(data[0]["log_text"][:1500])

print("\n=== Campione KRX/SGX ===")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange","in_universe":"eq.true","exchange":"in.(KRX,SGX)","limit":"10"})
sample = [(s["ticker"], s["exchange"]) for s in r2.json()]
for tk, ex in sample:
    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"  {tk}.{ex}:", r3.json())
