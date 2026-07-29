import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}

exchanges = ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE",
             "US","TSX","TSE","SEHK","ASX","KRX","SGX"]

total_filled = 0
total_notfound = 0
for ex in exchanges:
    us_r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"3000"})
    universe = set(r["ticker"] for r in us_r.json())
    if not universe: continue
    lp_r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{ex}","limit":"3000"})
    have = set(r["ticker"] for r in lp_r.json())
    missing = sorted(universe - have)
    if not missing: continue

    batch = []
    notfound = []
    for tk in missing:
        rpx = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"2"})
        rows_px = rpx.json()
        if not isinstance(rows_px, list) or len(rows_px) < 1:
            notfound.append(tk)
            continue
        last_row = rows_px[0]
        prev_row = rows_px[1] if len(rows_px) > 1 else None
        chg = round(last_row["adj_close"] / prev_row["adj_close"] - 1, 6) if (prev_row and prev_row.get("adj_close")) else None
        prev_price = (last_row["adj_close"] / (1 + chg)) if (chg is not None and (1 + chg) != 0) else None
        batch.append({"ticker": tk, "exchange": ex, "price": last_row["adj_close"],
                       "prev_price": prev_price, "price_date": last_row["date"], "change1d": chg})

    filled_here = 0
    for i in range(0, len(batch), 500):
        chunk = batch[i:i+500]
        r2 = requests.post(SUPABASE_URL + "/rest/v1/latest_prices?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk)
        if r2.status_code in (200, 201, 204):
            filled_here += len(chunk)
        else:
            print(f"  ERRORE batch {ex}: HTTP {r2.status_code} - {r2.text[:200]}")

    total_filled += filled_here
    total_notfound += len(notfound)
    print(f"{ex}: {len(missing)} assenti -> {filled_here} riempiti, {len(notfound)} non trovati nemmeno in prices_eod: {notfound[:20]}")

print(f"\nTOTALE: {total_filled} riempiti, {total_notfound} non trovati nemmeno nella fonte grezza (da investigare separatamente)")
