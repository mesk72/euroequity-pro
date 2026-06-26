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

print("="*50)
print("FIX COMBINED RANK — EU, APAC, US")
print("="*50)

MARKETS = [
    ("EU",   ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","LSE","AIM","SWX","OM","NGM","OB","CPSE"]),
    ("APAC", ["TSE","SEHK","ASX"]),
    ("US",   ["US"]),
]

for market, exchanges in MARKETS:
    print(f"\n{market}...")

    in_universe_set = set()
    for exchange in exchanges:
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker,exchange", "exchange": f"eq.{exchange}",
                        "in_universe": "eq.true", "limit": "1000", "offset": str(offset)})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            for d in batch:
                in_universe_set.add((d["ticker"], d["exchange"]))
            offset += 1000
            if len(batch) < 1000: break
    print(f"  In universe: {len(in_universe_set)}")

    all_data = []
    for exchange in exchanges:
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
                params={"select": "ticker,exchange,value_score,growth_score",
                        "exchange": f"eq.{exchange}",
                        "offset": str(offset), "limit": "1000"})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            all_data.extend(batch)
            offset += 1000
            if len(batch) < 1000: break

    all_data = [d for d in all_data if (d["ticker"], d["exchange"]) in in_universe_set]
    print(f"  Filtrati in_universe: {len(all_data)}")

    scored = [d for d in all_data
              if d.get("value_score") is not None and d.get("growth_score") is not None]
    print(f"  Con value+growth: {len(scored)}")

    if not scored:
        print(f"  SKIP — nessun titolo con score")
        continue

    comb_arr = [d["value_score"] + d["growth_score"] for d in scored]
    updates = [{
        "ticker": d["ticker"], "exchange": d["exchange"],
        "combined_rank": pct_rank(comb_arr, d["value_score"] + d["growth_score"])
    } for d in scored]

    ok = fail = 0
    for i in range(0, len(updates), 100):
        batch = updates[i:i+100]
        r = requests.post(SUPABASE_URL + "/rest/v1/fundamentals",
                          headers=headers_up, json=batch)
        if r.status_code in (200, 201, 204):
            ok += len(batch)
        else:
            fail += len(batch)
            print(f"  ERR {r.status_code}: {r.text[:200]}")

    print(f"  Scritti: ok={ok} fail={fail}")

print("\nFine")
