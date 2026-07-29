import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

exchanges = ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
             "US","TSX","TSE","SEHK","ASX","KRX","SGX"]
total = 0
per_ex = {}
for ex in exchanges:
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r | {"Prefer":"count=exact"},
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"1"})
    cr = rc.headers.get("content-range","0/0")
    cnt = int(cr.split("/")[-1]) if "/" in cr else 0
    per_ex[ex] = cnt
    total += cnt

groups = {
    "EUROPA": ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"],
    "US": ["US"], "TSX": ["TSX"],
    "TSE": ["TSE"], "SEHK": ["SEHK"], "ASX": ["ASX"], "KRX": ["KRX"], "SGX": ["SGX"],
}
for label, exs in groups.items():
    s = sum(per_ex[e] for e in exs)
    print(f"{label}: {s}  ({', '.join(f'{e}={per_ex[e]}' for e in exs)})")
print(f"\nTOTALE UNIVERSO REALE (in_universe=true, tabella stocks): {total}")

# ora confronta con quante righe esistono DAVVERO in latest_prices (non solo "ferme" - anche quelle ASSENTI del tutto)
print("\n=== righe in latest_prices vs universo, per vedere quante mancano DEL TUTTO ===")
tot_lp = 0
for ex in exchanges:
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r | {"Prefer":"count=exact"},
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"1"})
    cr = rc.headers.get("content-range","0/0")
    cnt = int(cr.split("/")[-1]) if "/" in cr else 0
    tot_lp += cnt
    diff = per_ex[ex] - cnt
    if diff != 0:
        print(f"  {ex}: universo={per_ex[ex]}, in latest_prices={cnt}, mancanti={diff}")
print(f"\nTotale righe in latest_prices: {tot_lp}  vs  universo reale: {total}  ->  mancanti del tutto: {total-tot_lp}")
