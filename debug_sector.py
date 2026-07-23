import os, requests, datetime
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker,title,pub_date,fetched_at","ticker":"eq.AAPL"})
print("Ora attuale UTC:", datetime.datetime.utcnow().isoformat())
print("Cutoff 24h fa:", (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat())
print()
for row in r.json():
    print(row)
