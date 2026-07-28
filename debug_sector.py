import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for script in ["daily_eu_yahoo", "daily_apac_yahoo"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
        params={"select":"log_text,created_at","script_name":f"eq.{script}","order":"created_at.desc","limit":"1"})
    data = r.json()
    print(f"=== {script} ===")
    if data:
        print(data[0]["log_text"][-2000:])
    else:
        print("NESSUN LOG TROVATO")
    print()
