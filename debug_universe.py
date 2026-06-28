import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# Test 1: leggi un titolo dal DB
print("=== TEST LETTURA STOCKS ===")
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,mkt_cap,company,sector,in_universe",
            "exchange":"eq.MIL","limit":"3"})
print(f"Status: {r.status_code}")
print(f"Risposta: {r.text[:500]}")

# Test 2: prova PATCH mkt_cap su un titolo noto
print("\n=== TEST PATCH MKT_CAP ===")
r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks",
    headers=headers_up,
    params={"ticker":"eq.ENI","exchange":"eq.MIL"},
    json={"mkt_cap": 50000.0})
print(f"Status: {r2.status_code}")
print(f"Risposta: {r2.text[:300]}")

# Test 3: leggi file TIKR da storage
print("\n=== TEST LETTURA TIKR EU ===")
r3 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    lines = r3.text.split("\n")
    print(f"Righe: {len(lines)}")
    print(f"Header: {lines[0][:200]}")
    print(f"Riga 1: {lines[1][:200]}")
else:
    print(f"Errore: {r3.text[:300]}")
