import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

# Conta righe distinte in news_cache (o tabella equivalente) aggiornate nell'ultima ora
r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker","limit":"1"})
print("Content-Range totale news_cache:", r.headers.get("content-range"))

import datetime
one_hour_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat()
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker","fetched_at":f"gte.{one_hour_ago}","limit":"1"})
print(f"Content-Range aggiornati ultima ora (dopo {one_hour_ago}):", r2.headers.get("content-range"))
