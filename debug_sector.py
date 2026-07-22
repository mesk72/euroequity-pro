import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r, params={"select":"ticker","limit":"1"})
print("Righe totali in news_cache:", r.headers.get("content-range"))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"ticker,exchange,pub_date,fetched_at","order":"fetched_at.desc","limit":"5"})
print("\nUltime 5 righe inserite:")
for row in r2.json():
    print(" ", row)
