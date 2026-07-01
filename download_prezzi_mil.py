import os, requests, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# Scarica 5 anni di storia
FROM_DATE = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
TO_DATE   = datetime.now().strftime("%Y-%m-%d")

EXCHANGE = "MIL"
LEEWAY_SUFFIX = ".MI"

print(f"=== DOWNLOAD PREZZI {EXCHANGE} DA LEEWAY ===")
print(f"Periodo: {FROM_DATE} → {TO_DATE}")
print()

# Carica titoli in universe per MIL
stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,yahoo_ticker","exchange":f"eq.{EXCHANGE}",
                "in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    stocks.extend(batch)
    offset += 1000
    if len(batch)<1000: break

print(f"Titoli in universe {EXCHANGE}: {len(stocks)}")

ok = fail = skip = 0
rows_to_insert = []

for s in stocks:
    ticker = s["ticker"]
    leeway_ticker = f"{ticker}{LEEWAY_SUFFIX}"

    url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={FROM_DATE}&to={TO_DATE}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            prices = r.json()
            for p in prices:
                adj_close = p.get("adjusted_close") or p.get("close")
                if not adj_close: continue
                rows_to_insert.append({
                    "ticker": ticker,
                    "exchange": EXCHANGE,
                    "date": p["date"],
                    "adj_close": float(adj_close)
                })
            ok += 1
            if ok % 10 == 0:
                print(f"  {ok}/{len(stocks)} OK — ultimo: {ticker} ({len(prices)} prezzi)")
        else:
            fail += 1
            print(f"  FAIL {ticker}: HTTP {r.status_code}")
    except Exception as e:
        fail += 1
        print(f"  FAIL {ticker}: {e}")

    time.sleep(0.5)  # 2 req/sec

print(f"\nDownload: ok={ok} fail={fail}")
print(f"Righe da inserire: {len(rows_to_insert)}")

# Prima cancella prezzi esistenti per MIL
print("\nCancello prezzi esistenti MIL...")
r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod",
    headers=headers_up,
    params={"exchange": "eq.MIL"})
print(f"Delete: {r.status_code}")

# Inserisci in batch da 500
print("Inserisco nuovi prezzi...")
BATCH = 500
inserted = 0
for i in range(0, len(rows_to_insert), BATCH):
    batch = rows_to_insert[i:i+BATCH]
    r = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
        headers={**headers_up, "Prefer": "resolution=merge-duplicates,return=minimal"},
        json=batch)
    if r.status_code in (200,201):
        inserted += len(batch)
    else:
        print(f"  FAIL batch {i}: {r.status_code} {r.text[:100]}")

print(f"Inseriti: {inserted}/{len(rows_to_insert)}")
print("\n=== DONE ===")
