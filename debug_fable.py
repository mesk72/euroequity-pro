import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

print("=" * 60)
print("[1] CONTEGGI in_universe=true (esatti)")
print("=" * 60)
for exch in ["US", "TSX", "KRX", "SGX"]:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}", "limit": "1"})
    print(f"  {exch}: {r.headers.get('content-range')}")

print()
print("=" * 60)
print("[2] CONTEGGI in_universe=true CON price non nullo")
print("=" * 60)
for exch in ["US", "KRX", "SGX"]:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}",
                "price": "not.is.null", "limit": "1"})
    print(f"  {exch}: {r.headers.get('content-range')}")

print()
print("=" * 60)
print("[3] VERIFICA REBUILD: prezzi Samsung/Hynix in prices_eod")
print("=" * 60)
for ticker in ["A005930", "A000660"]:
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_count,
        params={"select": "date", "ticker": f"eq.{ticker}", "exchange": "eq.KRX",
                "order": "date.desc", "limit": "2"})
    data = r.json()
    print(f"  {ticker}: totale={r.headers.get('content-range')} ultime date={[d['date'] for d in data] if isinstance(data, list) else 'ERR'}")

print()
print("=" * 60)
print("[4] TEST IPOTESI KOSDAQ: .KO vs .KQ su Leeway")
print("=" * 60)
# Ecopro BM, Alteogen, HLB: grandi KOSDAQ noti
kosdaq_tests = ["247540", "196170", "028300"]
for t in kosdaq_tests:
    for suffix in [".KO", ".KQ"]:
        url = f"{LEEWAY_BASE}/historicalquotes/{t}{suffix}?apitoken={LEEWAY_KEY}&from=2026-06-20&to=2026-07-05"
        try:
            resp = requests.get(url, timeout=15)
            n = len(resp.json()) if resp.status_code == 200 and isinstance(resp.json(), list) else 0
            print(f"  {t}{suffix}: HTTP {resp.status_code}, righe={n}")
        except Exception as e:
            print(f"  {t}{suffix}: ERRORE {e}")
    print()
