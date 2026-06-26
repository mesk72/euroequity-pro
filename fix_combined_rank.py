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

for market, ex_filter in [
    ("EU",   "not.in.(US,TSX,TSE,SEHK,ASX)"),
    ("APAC", "in.(TSE,SEHK,ASX)"),
]:
    print(f"\n{market}...")
    
    # Step 1: quanti titoli in universe
    r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,exchange,value_score,growth_score,combined_rank",
                "exchange": ex_filter, "in_universe": "eq.true",
                "limit": "5", "order": "value_score.desc.nullslast"})
    sample = r.json()
    print(f"  Sample top 5 by value_score:")
    if isinstance(sample, list):
        for d in sample:
            print(f"    {d['ticker']}/{d['exchange']}: val={d.get('value_score')} grw={d.get('growth_score')} best={d.get('combined_rank')}")
    else:
        print(f"  ERR: {sample}")
        continue

    # Step 2: carica tutti
    all_data = []
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
            params={"select": "ticker,exchange,value_score,growth_score",
                    "exchange": ex_filter, "in_universe": "eq.true",
                    "offset": str(offset), "limit": "1000"})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_data.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
    print(f"  Totale: {len(all_data)}")

    scored = [d for d in all_data
              if d.get("value_score") is not None and d.get("growth_score") is not None]
    print(f"  Con entrambi gli score: {len(scored)}")

    if not scored:
        print(f"  PROBLEMA: value_score e growth_score sono NULL nel DB!")
        print(f"  Serve rieseguire weekly_{'eu' if market=='EU' else 'apac'}.py")
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
        if r.status_code in (200, 201, 204): ok += len(batch)
        else:
            fail += len(batch)
            print(f"  ERR {r.status_code}: {r.text[:200]}")

    print(f"  Scritti: ok={ok} fail={fail}")

print("\nFine")
