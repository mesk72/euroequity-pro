import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for exch in ["LSE","MIL"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"1"})
    print(f"{exch} in_universe: {r.headers.get('content-range')}")

# quanti hanno un valore 'price' popolato in fundamentals (quello che il sito legge)
for exch in ["LSE","MIL"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_count,
        params={"select":"ticker","exchange":f"eq.{exch}","price":"not.is.null","limit":"1"})
    print(f"{exch} fundamentals.price NOT NULL: {r.headers.get('content-range')}")

# campione date prezzo grezze
for t,ex in [("VOD","LSE"),("ENI","MIL")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{t}.{ex} ultima data prices_eod: {r.json()}")
