import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

for exs in [["TSE"], ["SEHK"], ["ASX"], ["KRX"], ["SGX"], ["TSE","SEHK","ASX"], ["TSE","SEHK","ASX","KRX","SGX"]]:
    ex_filter = ",".join(exs)
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"in.({ex_filter})","in_universe":"eq.true","limit":"1"})
    print(f"{exs}: {r.headers.get('content-range')}")
