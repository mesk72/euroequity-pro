import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

tables = ["prices_eod", "fundamentals", "stocks", "watchlist"]
for t in tables:
    r = requests.head(f"{SUPABASE_URL}/rest/v1/{t}", headers=headers_r, params={"select":"*"})
    content_range = r.headers.get("Content-Range", "")
    count = content_range.split("/")[-1] if "/" in content_range else "?"
    print(f"{t}: {count} righe")
