import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US",
             "date":"gte.2026-05-25","order":"date.asc","limit":"60"})
rows = r.json()
print(f"Righe trovate: {len(rows)}")
for row in rows:
    print(f"  {row['date']}: {row['adj_close']}")
