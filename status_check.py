import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

print("=" * 60)
print("CONTEGGI in_universe=true PER EXCHANGE")
print("=" * 60)
exchanges = ["US","TSX","KRX","SGX","AS","MC","BR","HE","CPSE","OB","GR",
             "LSE","XETRA","PA","OM","SWX","MIL","VI","IR","LS",
             "TSE","SEHK","ASX"]
for ex in exchanges:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{ex}","limit":"1"})
    cr = r.headers.get("content-range","?")
    print(f"  {ex}: {cr}")

print()
print("=" * 60)
print("STORICO PREZZI: campione KRX (KOSDAQ .KQ) — profondita' in giorni")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,primary_exchange","exchange":"eq.KRX",
            "in_universe":"eq.true","primary_exchange":"eq.KOSDAQ","limit":"8"})
kosdaq_sample = r.json() if isinstance(r.json(), list) else []
print(f"Campione KOSDAQ in universe: {len(kosdaq_sample)} testati")
for s in kosdaq_sample:
    t = s["ticker"]
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_count,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.KRX","limit":"1"})
    cr = rc.headers.get("content-range","")
    tot = cr.split("/")[-1] if "/" in cr else "?"
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.KRX","order":"date.asc","limit":"1"})
    d2 = r2.json()
    oldest = d2[0]["date"] if isinstance(d2,list) and d2 else "N/A"
    print(f"  {t}: {tot} righe totali, prima data={oldest}")

print()
print("=" * 60)
print("STORICO PREZZI: campione SGX — profondita'")
print("=" * 60)
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.SGX","in_universe":"eq.true","limit":"6"})
sgx_sample = r.json() if isinstance(r.json(), list) else []
for s in sgx_sample:
    t = s["ticker"]
    rc = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_count,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.SGX","limit":"1"})
    cr = rc.headers.get("content-range","")
    tot = cr.split("/")[-1] if "/" in cr else "?"
    print(f"  {t}: {tot} righe totali")

print()
print("FATTO.")
