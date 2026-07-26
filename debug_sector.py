import os, requests, time
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"150","order":"ticker"})
chunk = [s["ticker"] for s in r.json()]

from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
t0 = time.time()
total_rows = 0
offset_p = 0
pages = 0
while True:
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select": "ticker,date,adj_close", "exchange": "eq.US",
                "ticker": f"in.({','.join(chunk)})", "date": f"gte.{from_400d}",
                "order": "ticker,date.desc", "limit": "1000", "offset": str(offset_p)})
    batch = rp.json()
    pages += 1
    if not isinstance(batch, list) or not batch: break
    total_rows += len(batch)
    offset_p += 1000
    if len(batch) < 1000: break

elapsed = time.time() - t0
print(f"TEMPO FASE 3 per 150 titoli: {elapsed:.1f}s, {pages} pagine, {total_rows} righe totali")
