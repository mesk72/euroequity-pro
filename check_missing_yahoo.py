import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

exchanges = ["US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS","TSE","SEHK","ASX","KRX","SGX"]
total_missing = 0
for ex in exchanges:
    r = requests.head(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"*","exchange":f"eq.{ex}","in_universe":"eq.true","yahoo_ticker":"is.null"})
    cr = r.headers.get("Content-Range","")
    count = cr.split("/")[-1] if "/" in cr else "?"
    if count not in ("0","?"):
        print(f"{ex}: {count} titoli senza yahoo_ticker")
        try:
            total_missing += int(count)
        except: pass
print(f"\nTOTALE mancanti: {total_missing}")
