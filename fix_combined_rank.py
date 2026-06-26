import os, math, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

def pct_rank(vals, v):
    if v is None or not vals: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    below = sum(1 for x in vals if x < v)
    return max(1, min(99, int(round(below / len(vals) * 100))))

print("Fix combined_rank per EU e APAC")
print("="*50)

for market, exchange_filter in [
    ("EU",   {"exchange": "not.in.(US,TSX,TSE,SEHK,ASX)"}),
    ("APAC", {"exchange": "in.(TSE,SEHK,ASX)"}),
]:
    print(f"\n{market}...")
    all_data = []
    offset = 0
    while True:
        params = {"select": "ticker,exchange,value_score,growth_score",
                  "in_universe": "eq.true",
                  "offset": str(offset), "limit": "1000"}
        params.update(exchange_filter)
        r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals",
                         headers=headers_r, params=params)
        data = r.json()
        if not isinstance(data, list) or not data: break
        all_data.extend(data)
        offset += 1000
        if len(data) < 1000: break

    print(f"  Letti: {len(all_data)} titoli")

    scored = [d for d in all_data
              if d.get('value_score') is not None and d.get('growth_score') is not None]
    print(f"  Con value+growth score: {len(scored)}")

    if not scored:
        print(f"  NESSUN DATO — impossibile calcolare combined_rank")
        continue

    comb_arr = [d['value_score'] + d['growth_score'] for d in scored]

    updates = []
    for d in scored:
        s = d['value_score'] + d['growth_score']
        updates.append({
            "ticker": d['ticker'],
            "exchange": d['exchange'],
            "combined_rank": pct_rank(comb_arr, s)
        })

    ok = 0
    for i in range(0, len(updates), 100):
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals",
                          headers=headers_up, json=updates[i:i+100])
        if r.status_code in (200, 201, 204):
            ok += len(updates[i:i+100])

    print(f"  Combined rank scritti: {ok}/{len(updates)}")

print("\nFix completato")
