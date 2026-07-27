import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"log_text,created_at","order":"created_at.desc","limit":"3"})
for row in r.json():
    print(row.get("created_at"), "-", (row.get("log_text") or "")[:100])
