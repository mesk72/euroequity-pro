import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for tk, ex in [("7203","TSE"), ("9984","TSE"), ("0700","SEHK"), ("BHP","ASX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}.{ex}:", r.json())
