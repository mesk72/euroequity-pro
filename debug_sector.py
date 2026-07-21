import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/watchlist", headers=headers_r,
    params={"select":"*","order":"added_at.desc","limit":"20"})
print("Ultime 20 righe in watchlist:")
for row in r.json():
    print(row)
