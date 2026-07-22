import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r, params={"select":"ticker","limit":"1"})
print("Righe in news_cache ora:", r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"ticker,fetched_at","order":"fetched_at.desc","limit":"3"})
print("Ultime righe:", r2.json())
