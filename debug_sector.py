import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/daily_log", headers=headers_r,
    params={"select":"run_date,market,prices_updated,prices_failed,duration_seconds,created_at","order":"created_at.desc","limit":"15"})
for row in r.json():
    print(row)
