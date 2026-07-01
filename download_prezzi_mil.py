import os, requests, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EXCHANGE      = "MIL"
LEEWAY_SUFFIX = ".MI"
TO_DATE       = datetime.now().strftime("%Y-%m-%d")
FROM_5Y       = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")

print(f"=== DOWNLOAD 5 ANNI PREZZI {EXCHANGE} DA LEEWAY ===")
print(f"Periodo: {FROM_5Y} → {TO_DATE}")
print()

# Carica titoli in universe
stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{EXCHANGE}",
                "in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    stocks.extend([s["ticker"] for s in batch])
    offset += 1000
    if len(batch)<1000: break

print(f"Titoli in universe {EXCHANGE}: {len(stocks)}")

# Cancella tutti i prezzi esistenti per MIL
print(f"Cancello prezzi esistenti {EXCHANGE}...")
r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod",
    headers=headers_up,
    params={"exchange": f"eq.{EXCHANGE}"})
print(f"Delete: HTTP {r.status_code}")

# Scarica 5 anni per ogni titolo
ok = fail = 0
rows_to_insert = []

for i, ticker in enumerate(stocks):
    leeway_ticker = f"{ticker}{LEEWAY_SUFFIX}"
    url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TO_DATE}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            prices = r.json()
            for p in prices:
                adj_close = p.get("adjusted_close") or p.get("close")
                if not adj_close: continue
                rows_to_insert.append({
                    "ticker": ticker, "exchange": EXCHANGE,
                    "date": p["date"], "adj_close": float(adj_close)
                })
            ok += 1
            print(f"  [{i+1}/{len(stocks)}] {ticker}: {len(prices)} prezzi OK")
        else:
            fail += 1
            print(f"  [{i+1}/{len(stocks)}] {ticker}: FAIL HTTP {r.status_code}")
    except Exception as e:
        fail += 1
        print(f"  [{i+1}/{len(stocks)}] {ticker}: ERROR {e}")

    # Inserisci ogni 50 titoli per non perdere dati se il job si interrompe
    if len(rows_to_insert) >= 5000:
        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers={**headers_up, "Prefer":"resolution=merge-duplicates,return=minimal"},
            json=rows_to_insert)
        print(f"  >>> Inserite {len(rows_to_insert)} righe: HTTP {r2.status_code}")
        rows_to_insert = []

    time.sleep(0.5)

# Inserisci righe rimanenti
if rows_to_insert:
    r2 = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
        headers={**headers_up, "Prefer":"resolution=merge-duplicates,return=minimal"},
        json=rows_to_insert)
    print(f"  >>> Inserite {len(rows_to_insert)} righe finali: HTTP {r2.status_code}")

print(f"\n=== DONE: ok={ok} fail={fail} ===")
