import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
                "Prefer": "count=exact"}

exchanges = ["MIL","XETRA","PA","LSE","OM","SWX","OB","AS","MC","BR",
             "CPSE","HE","VI","IR","LS","US","TSX","TSE","SEHK","ASX"]

print(f"{'Exchange':<8} {'Totale':>8} {'Con Yahoo':>10} {'Senza':>8}")
print("-" * 40)

for ex in exchanges:
    r1 = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker", "in_universe": "eq.true",
                "exchange": "eq." + ex, "limit": "1"})
    total = int(r1.headers.get("content-range","0/0").split("/")[-1])

    r2 = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker", "in_universe": "eq.true",
                "exchange": "eq." + ex, "yahoo_ticker": "not.is.null", "limit": "1"})
    with_y = int(r2.headers.get("content-range","0/0").split("/")[-1])

    print(f"{ex:<8} {total:>8} {with_y:>10} {total-with_y:>8}")
