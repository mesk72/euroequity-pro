import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.OB","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break
print(f"Universo Norvegia (OB): {len(universe)} titoli")

pe_values = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,pe_forward","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe and d.get("pe_forward") is not None and d["pe_forward"] > 0:
            pe_values.append(d["pe_forward"])
    offset += 1000
    if len(batch) < 1000: break

pe_values.sort()
print(f"Titoli con PE NTM positivo valido: {len(pe_values)}")

target = 15.0
below = sum(1 for v in pe_values if v < target)
rank_pct = round(below / len(pe_values) * 100)
print(f"\nUn PE NTM di {target} sarebbe piu' basso di {below}/{len(pe_values)} titoli")
print(f"Rank percentile stimato: {rank_pct}")
print(f"\nDistribuzione: min={pe_values[0]:.2f}, mediana={pe_values[len(pe_values)//2]:.2f}, max={pe_values[-1]:.2f}")
