import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for t in ['HLF', 'TAL']:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,pb,pe_trailing,pe_forward","ticker":f"eq.{t}","exchange":"eq.US"})
    print(f"{t}.US ora:", r.json())
