import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

groups = {
    "EU": ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"],
    "US": ["US"],
    "TSX": ["TSX"],
    "KRX": ["KRX"],
}
for label, exchanges in groups.items():
    all_rows = []
    for ex in exchanges:
        offset = 0
        while True:
            r = requests.get(f"{SUPABASE_URL}/rest/v1/latest_prices", headers=headers_r,
                params={"select":"ticker,exchange,price_date","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
            rows = r.json()
            if not isinstance(rows, list) or not rows: break
            all_rows.extend(rows)
            offset += 1000
            if len(rows) < 1000: break
    dates = Counter(r["price_date"] for r in all_rows)
    top_date = dates.most_common(1)[0][0] if dates else None
    stale = [r for r in all_rows if r["price_date"] != top_date]
    print(f"{label}: {len(all_rows)} righe, prevalente={top_date}, distribuzione={dict(dates.most_common(5))}")
    if stale:
        print(f"  -> {len(stale)} fermi: {[(s['ticker'],s['exchange'],s['price_date']) for s in stale[:15]]}")
