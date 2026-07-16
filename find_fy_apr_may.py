import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,fiscal_month","exchange":"eq.US","fiscal_month":"not.is.null","limit":"1000"})
data = r.json()
print(f"Totale con fiscal_month popolato: {len(data)}")
from collections import Counter
c = Counter(d["fiscal_month"] for d in data)
print("Distribuzione:", dict(c))

for month in [4,5]:
    matches = [d for d in data if d["fiscal_month"]==month]
    print(f"\nMese {month}: {len(matches)} titoli")
    for m in matches[:5]:
        print(f"  {m}")
