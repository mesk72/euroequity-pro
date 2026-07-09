import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# prendi un ticker US reale senza website
r0 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange","exchange":"eq.US","in_universe":"eq.true","website":"is.null","limit":"1"})
target = r0.json()
print("Titolo test:", target)
if target:
    t = target[0]
    payload = [{"ticker": t["ticker"], "exchange": t["exchange"], "website": "https://test-example.com"}]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up, json=payload)
    print(f"HTTP {r.status_code}")
    print(r.text[:500])
