import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== US ===")
for tk, ex in [("AAPL","US"), ("NVDA","US")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}:", r.json())

print("\n=== EU ===")
for tk, ex in [("SAP","XETRA"), ("MC","PA")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}:", r.json())

print("\n=== APAC ===")
for tk, ex in [("7203","TSE"), ("9984","TSE"), ("BHP","ASX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}:", r.json())
