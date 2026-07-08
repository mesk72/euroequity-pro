import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

print("=" * 60)
print("DIAGNOSTICA KRX/SGX")
print("=" * 60)

for ex in ["KRX", "SGX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "exchange": f"eq.{ex}", "limit": "1"})
    print(f"\n{ex} TOTALE righe (qualsiasi in_universe): {r.headers.get('content-range')} status={r.status_code}")

    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "exchange": f"eq.{ex}", "in_universe": "eq.true", "limit": "1"})
    print(f"{ex} in_universe=true: {r2.headers.get('content-range')} status={r2.status_code}")

    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "exchange": f"eq.{ex}", "in_universe": "eq.false", "limit": "1"})
    print(f"{ex} in_universe=false: {r3.headers.get('content-range')} status={r3.status_code}")

    r4 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "exchange": f"eq.{ex}", "in_universe": "is.null", "limit": "1"})
    print(f"{ex} in_universe=NULL: {r4.headers.get('content-range')} status={r4.status_code}")

    r5 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,in_universe,primary_exchange", "exchange": f"eq.{ex}", "limit": "5"})
    print(f"{ex} campione 5 righe: {r5.text[:600]}")

print()
print("=" * 60)
print("VALORI DISTINTI DI exchange NELLA TABELLA stocks")
print("=" * 60)
r6 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select": "exchange", "limit": "5000"})
data = r6.json() if isinstance(r6.json(), list) else []
distinct = sorted(set(row.get("exchange") for row in data))
print(distinct)
print(f"(status={r6.status_code}, campione {len(data)} righe)")

print("\nFATTO.")
