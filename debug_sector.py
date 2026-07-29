import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

groups = {
    "EUROPA": ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"],
    "NORD AMERICA (US)": ["US"],
    "NORD AMERICA (TSX)": ["TSX"],
    "APAC - Giappone (TSE)": ["TSE"],
    "APAC - Hong Kong (SEHK)": ["SEHK"],
    "APAC - Australia (ASX)": ["ASX"],
    "APAC - Corea (KRX)": ["KRX"],
    "APAC - Singapore (SGX)": ["SGX"],
}
grand_total = 0
grand_stale = 0
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
    grand_total += len(all_rows)
    grand_stale += len(stale)
    pct = (len(stale)/len(all_rows)*100) if all_rows else 0
    print(f"{label}: {len(all_rows)} titoli totali, {len(stale)} fermi ({pct:.1f}%), data attesa={top_date}")

print(f"\nTOTALE COMPLESSIVO: {grand_total} titoli, {grand_stale} fermi ({grand_stale/grand_total*100:.1f}%)")
