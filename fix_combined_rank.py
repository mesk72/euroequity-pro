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
print("FIX COMBINED RANK — EU e APAC")
print("="*50)

for market, ex_filter in [
    ("EU",   "not.in.(US,TSX,TSE,SEHK,ASX)"),
    ("APAC", "in.(TSE,SEHK,ASX)"),
]:
    print(f"\n{market}...")
    all_data = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
            params={"select": "ticker,exchange,value_score,growth_score",
                    "exchange": ex_filter, "in_universe": "eq.true",
                    "offset": str(offset), "limit": "1000"})
        batch = r.json()
        print(f"  offset={offset} status={r.status_code} n={len(batch) if isinstance(batch,list) else batch}")
        if not isinstance(batch, list) or not batch: break
        all_data.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    print(f"  Totale letti: {len(all_data)}")

    scored = [d for d in all_data
              if d.get("value_score") is not None and d.get("growth_score") is not None]
    print(f"  Con value+growth: {len(scored)}")

    if not scored:
        print(f"  SKIP — nessun titolo con entrambi gli score")
        continue

    comb_arr = [d["value_score"] + d["growth_score"] for d in scored]

    updates = [{
        "ticker": d["ticker"],
        "exchange": d["exchange"],
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
            print(f"  ERR batch {i}: {r.status_code} {r.text[:100]}")

    print(f"  Combined rank scritti: ok={ok} fail={fail}")
    
    # Verifica
    r_check = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,combined_rank",
                "exchange": ex_filter, "in_universe": "eq.true",
                "combined_rank": "not.is.null", "limit": "3",
                "order": "combined_rank.desc"})
    sample = r_check.json()
    if isinstance(sample, list):
        for d in sample:
            print(f"  CHECK {d['ticker']}/{d['exchange']}: best={d['combined_rank']}")

print("\nFix completato")
