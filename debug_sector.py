import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# TSX ha dati in prices_eod?
for ex in ["US","TSX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r | {"Prefer":"count=exact"},
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"1"})
    cnt = r2.headers.get("content-range","0/0").split("/")[-1]
    print(f"{ex}: ultima data={r.json()}, righe totali in prices_eod={cnt}")

# quanti in_universe per US vs TSX separatamente
for ex in ["US","TSX"]:
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r | {"Prefer":"count=exact"},
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"1"})
    cnt = rc.headers.get("content-range","0/0").split("/")[-1]
    print(f"{ex}: universo in_universe=true -> {cnt}")

# latest_prices per US vs TSX separatamente
for ex in ["US","TSX"]:
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r | {"Prefer":"count=exact"},
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"1"})
    cnt = rc.headers.get("content-range","0/0").split("/")[-1]
    print(f"{ex}: righe in latest_prices -> {cnt}")
