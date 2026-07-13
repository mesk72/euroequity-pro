import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
for t, ex in [("NVDA","US"), ("SIM0","XETRA")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mom1w","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    d = r.json()
    if d:
        v = d[0]['mom1w']
        print(f"{t}.{ex}: mom1w={v} -> {v*100:.2f}%" if v is not None else f"{t}.{ex}: mom1w=None")
