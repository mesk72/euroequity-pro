import os, requests, csv, io
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

print("=" * 60)
print("[A] STATO PREZZI US ATTUALE (diretto da DB)")
print("=" * 60)
for t in ["JPM","AAPL","MSFT","TSLA"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"3"})
    print(f"  {t}.US ultime 3 date: {[d['date'] for d in r.json()] if isinstance(r.json(),list) else r.text[:100]}")

print()
print("=" * 60)
print("[B] TEST DIRETTO LEEWAY per JPM (indipendente dallo script)")
print("=" * 60)
to_d = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
url = f"{LEEWAY_BASE}/historicalquotes/JPM?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
resp = requests.get(url, timeout=15)
print(f"  HTTP {resp.status_code}")
print(f"  Body: {resp.text[:500]}")

print()
print("=" * 60)
print("[C] MARKET CAP APAC — sample piu' ampio da fundamentals")
print("=" * 60)
for exch in ["TSE","SEHK","ASX","KRX","SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"5"})
    tickers = [s["ticker"] for s in r.json()] if isinstance(r.json(),list) else []
    print(f"  --- {exch} (campione) ---")
    for t in tickers:
        rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,mkt_cap","ticker":f"eq.{t}","exchange":f"eq.{exch}"})
        d = rf.json()
        print(f"    {t}.{exch}: fundamentals={d}")

print()
print("=" * 60)
print("[D] RAW TIKR APAC per lo stesso campione — per capire se il")
print("    problema e' nel merge/join ticker o nel valore stesso")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
rows_by_ticker = {}
for row in reader:
    rows_by_ticker[row.get("Ticker","").strip()] = row
for exch in ["TSE","SEHK","ASX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"3"})
    tickers = [s["ticker"] for s in r.json()] if isinstance(r.json(),list) else []
    for t in tickers:
        row = rows_by_ticker.get(t)
        print(f"    {t}.{exch}: presente in TIKR={row is not None}"
              + (f", raw mktcap={row.get('Last Mkt Cap')!r}, PrimaryExch={row.get('Primary Exchange')!r}" if row else ""))

print("\nFATTO.")
