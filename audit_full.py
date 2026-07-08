import os, requests, csv, io, math
from datetime import datetime

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

def get_mkt_cap(ticker, exchange):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"mkt_cap","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","limit":"1"})
    d = r.json()
    return d[0]["mkt_cap"] if isinstance(d,list) and d else None

def max_price_date(ticker, exchange):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                "order":"date.desc","limit":"1"})
    d = r.json()
    return d[0]["date"] if isinstance(d,list) and d else "NESSUNA"

print("=" * 60)
print("[1] MARKET CAP: valore attuale in fundamentals (PRIMA del")
print("    prossimo run weekly che applichera' il fix)")
print("=" * 60)
for t, ex in [("JPM","US"),("AAPL","US"),("7203","TSE"),("0700","SEHK"),("BHP","ASX")]:
    mc = get_mkt_cap(t, ex)
    print(f"  {t}.{ex}: mkt_cap DB = {mc}")

print()
print("=" * 60)
print("[2] RAW TIKR — valore grezzo per confronto (US)")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
for row in reader:
    if row.get("Ticker","").strip() in ("JPM","AAPL"):
        print(f"  {row.get('Ticker')}: raw 'Last Mkt Cap' = {row.get('Last Mkt Cap')!r}")

print()
print("=" * 60)
print("[3] RAW TIKR APAC — valore grezzo per confronto")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
for row in reader:
    if row.get("Ticker","").strip() in ("7203","0700","BHP"):
        print(f"  {row.get('Ticker')}: raw 'Last Mkt Cap' = {row.get('Last Mkt Cap')!r}")

print()
print("=" * 60)
print("[4] STATO KRX/SGX in_universe (post run di oggi)")
print("=" * 60)
for exch in ["KRX", "SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"1"})
    print(f"  {exch} in_universe: {r.headers.get('content-range')}")

print()
print("=" * 60)
print("[5] STATO PREZZI KRX/SGX in prices_eod (campione)")
print("=" * 60)
for exch in ["KRX", "SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"3"})
    tickers = [s["ticker"] for s in r.json()] if isinstance(r.json(), list) else []
    for t in tickers:
        print(f"  {t}.{exch}: ultima data prezzo = {max_price_date(t, exch)}")

print()
print("=" * 60)
print("[6] STATO PREZZI EU (prima del fix daily_eu appena lanciato)")
print("=" * 60)
for t, ex in [("ASML","AS"),("SAP","XETRA"),("BNP","PA"),("NESN","SWX")]:
    print(f"  {t}.{ex}: ultima data prezzo = {max_price_date(t, ex)}")

print()
print("=" * 60)
print("[7] US in_universe count (verifica retry fix)")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","in_universe":"eq.true","exchange":"eq.US","limit":"1"})
print(f"  US in_universe: {r.headers.get('content-range')}")

print("\nFATTO.")
