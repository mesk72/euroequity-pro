import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"created_at,log_text","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"})
logs = r.json()
if logs:
    print("created_at:", logs[0]["created_at"])
    print(logs[0]["log_text"])
else:
    print("nessun log trovato")
