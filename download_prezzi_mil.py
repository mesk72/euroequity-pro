import os, requests, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EXCHANGE     = "MIL"
LEEWAY_SUFFIX = ".MI"
TO_DATE      = datetime.now().strftime("%Y-%m-%d")
FROM_5Y      = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
SPLIT_THRESHOLD = 0.15  # 15% differenza = probabile split

print(f"=== DOWNLOAD PREZZI {EXCHANGE} DA LEEWAY ===")
print(f"Data odierna: {TO_DATE}")
print()

# Carica titoli in universe per MIL
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

# Carica ultimo prezzo in DB per ogni titolo
print("Carico ultimi prezzi dal DB...")
last_price_db = {}
for ticker in stocks:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}",
                "exchange":f"eq.{EXCHANGE}","order":"date.desc","limit":"1"})
    rows = r.json()
    if isinstance(rows,list) and rows:
        last_price_db[ticker] = rows[0]

print(f"  Con prezzi in DB: {len(last_price_db)}")
print(f"  Senza prezzi in DB: {len(stocks)-len(last_price_db)}")

ok = fail = split_detected = 0
rows_to_insert = []
to_delete_full = []  # ticker con split — cancella tutto e riscarica

for ticker in stocks:
    leeway_ticker = f"{ticker}{LEEWAY_SUFFIX}"
    last_db = last_price_db.get(ticker)

    # Determina from_date
    if last_db:
        last_date_db = last_db["date"]
        from_date = (datetime.strptime(last_date_db, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        last_close_db = last_db.get("adj_close") or 0
    else:
        # Nessun prezzo in DB — scarica 5 anni
        from_date = FROM_5Y
        last_date_db = None
        last_close_db = 0

    if from_date > TO_DATE:
        skip_msg = "prezzi aggiornati"
        # Controlla comunque split — scarica solo ultimo prezzo
        from_date_check = (datetime.strptime(TO_DATE, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
        url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={from_date_check}&to={TO_DATE}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200 and isinstance(r.json(), list) and r.json():
                prices = sorted(r.json(), key=lambda x: x["date"])
                # Trova prezzo Leeway per ultima data in DB
                leeway_on_last_db = next((p for p in prices if p["date"] == last_date_db), None)
                if leeway_on_last_db and last_close_db:
                    leeway_close = leeway_on_last_db.get("adjusted_close") or leeway_on_last_db.get("close") or 0
                    if leeway_close and abs(leeway_close - last_close_db) / last_close_db > SPLIT_THRESHOLD:
                        print(f"  SPLIT DETECTED {ticker}: DB={last_close_db:.2f} Leeway={leeway_close:.2f}")
                        to_delete_full.append(ticker)
                        split_detected += 1
        except: pass
        time.sleep(0.5)
        continue

    url = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={from_date}&to={TO_DATE}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            prices = r.json()

            # Controlla split — confronta prezzo Leeway su last_date_db con DB
            if last_close_db and last_date_db:
                leeway_on_last_db = next((p for p in prices if p["date"] == last_date_db), None)
                if leeway_on_last_db:
                    leeway_close = leeway_on_last_db.get("adjusted_close") or leeway_on_last_db.get("close") or 0
                    if leeway_close and abs(leeway_close - last_close_db) / last_close_db > SPLIT_THRESHOLD:
                        print(f"  SPLIT DETECTED {ticker}: DB={last_close_db:.2f} Leeway={leeway_close:.2f}")
                        to_delete_full.append(ticker)
                        split_detected += 1
                        # Riscarica 5 anni
                        url5y = f"{LEEWAY_BASE}/historicalquotes/{leeway_ticker}?apitoken={LEEWAY_KEY}&from={FROM_5Y}&to={TO_DATE}"
                        r5y = requests.get(url5y, timeout=15)
                        if r5y.status_code == 200 and isinstance(r5y.json(), list):
                            prices = r5y.json()
                        time.sleep(0.5)

            for p in prices:
                adj_close = p.get("adjusted_close") or p.get("close")
                if not adj_close: continue
                rows_to_insert.append({
                    "ticker": ticker, "exchange": EXCHANGE,
                    "date": p["date"], "adj_close": float(adj_close)
                })
            ok += 1
            if ok % 20 == 0 or len(last_price_db.get(ticker,{})) == 0:
                print(f"  {ok}/{len(stocks)} {ticker}: {len(prices)} righe (from={from_date})")
        else:
            fail += 1
            print(f"  FAIL {ticker}: HTTP {r.status_code}")
    except Exception as e:
        fail += 1
        print(f"  FAIL {ticker}: {e}")

    time.sleep(0.5)

print(f"\nDownload: ok={ok} fail={fail} split={split_detected}")
print(f"Righe da inserire: {len(rows_to_insert)}")

# Cancella prezzi per titoli con split
if to_delete_full:
    print(f"\nCancello prezzi per {len(to_delete_full)} titoli con split...")
    for ticker in to_delete_full:
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers=headers_up,
            params={"ticker":f"eq.{ticker}","exchange":f"eq.{EXCHANGE}"})
        print(f"  Delete {ticker}: {r.status_code}")

# Inserisci in batch da 500
if rows_to_insert:
    print(f"\nInserisco {len(rows_to_insert)} prezzi...")
    BATCH = 500
    inserted = 0
    for i in range(0, len(rows_to_insert), BATCH):
        batch = rows_to_insert[i:i+BATCH]
        r = requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers={**headers_up, "Prefer":"resolution=merge-duplicates,return=minimal"},
            json=batch)
        if r.status_code in (200,201):
            inserted += len(batch)
        else:
            print(f"  FAIL batch {i}: {r.status_code} {r.text[:100]}")
    print(f"Inseriti: {inserted}/{len(rows_to_insert)}")

print("\n=== DONE ===")
