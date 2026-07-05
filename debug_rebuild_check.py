import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

test_tickers = [("A005930", "KRX"), ("A000660", "KRX"), ("A009150", "KRX")]

for ticker, exchange in test_tickers:
    r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "date,adj_close", "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}",
                "order": "date.desc", "limit": "5"})
    data = r.json()
    print(f"{ticker} ({exchange}): {len(data) if isinstance(data, list) else 'ERRORE'} righe (ultime 5 mostrate)")
    if isinstance(data, list):
        for d in data:
            print(f"    {d}")
    print()

# Conteggio totale righe prices_eod per KRX
headers_count = {**headers_r, "Prefer": "count=exact"}
r2 = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_count,
    params={"select": "ticker", "exchange": "eq.KRX", "limit": "1"})
print("Conteggio totale righe KRX in prices_eod:", r2.headers.get("content-range"))

headers_count2 = {**headers_r, "Prefer": "count=exact"}
r3 = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_count2,
    params={"select": "ticker", "exchange": "eq.SGX", "limit": "1"})
print("Conteggio totale righe SGX in prices_eod:", r3.headers.get("content-range"))
